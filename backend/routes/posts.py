"""
文章路由模块
提供文章的增删改查 API 接口（含置顶功能）
"""
from datetime import datetime, timezone
from typing import List, Optional
import json

import models
import auth
from media_usage import sync_post_media, refresh_media_usage_counts
from database import get_db, settings
from cache import posts_cache, make_cache_key, invalidate_posts_cache
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 创建路由器
router = APIRouter(prefix="/posts", tags=["文章管理"])

# OAuth2 密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
VALID_STATUSES = {"draft", "published", "scheduled"}


# ============== 认证依赖 ==============

async def get_current_user(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)
):
    """
    验证 JWT Token 并获取当前用户

    Args:
        authorization: HTTP Authorization 请求头
        db: 数据库会话

    Returns:
        Admin: 当前登录的管理员对象

    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    # 检查 Authorization 头
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 提取 token
    token = authorization.split(" ")[1]

    try:
        # 解码 JWT
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的认证信息")
    except JWTError:
        raise HTTPException(status_code=401, detail="认证信息已过期或无效")

    # 查询用户
    user = db.query(models.Admin).filter(
        models.Admin.username == username
    ).first()

    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


def normalize_status(requested_status: Optional[str], is_draft: bool) -> str:
    """根据请求参数计算最终文章状态"""
    if requested_status:
        status = requested_status.lower().strip()
    else:
        status = "draft" if is_draft else "published"

    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="无效的文章状态")
    return status


def normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """将日期时间统一为 UTC"""
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def process_scheduled_posts(db: Session) -> None:
    """检查定时文章并在到点后自动发布"""
    now = datetime.utcnow()
    scheduled_posts = db.query(models.Post).filter(
        models.Post.status == "scheduled",
        models.Post.scheduled_at != None,
        models.Post.scheduled_at <= now
    ).all()

    if not scheduled_posts:
        return

    for post in scheduled_posts:
        scheduled_time = post.scheduled_at
        try:
            post.status = "published"
            post.is_draft = 0
            post.published_at = scheduled_time or now
            post.scheduled_at = None
            db.add(models.ScheduledPublishLog(
                post_id=post.id,
                status="success",
                message="发布成功",
                scheduled_at=scheduled_time
            ))
            db.commit()
        except Exception as exc:
            db.rollback()
            db.add(models.ScheduledPublishLog(
                post_id=post.id,
                status="failed",
                message=str(exc)[:500],
                scheduled_at=scheduled_time
            ))
            db.commit()


def create_revision_snapshot(
    db: Session,
    post_obj: models.Post,
    editor: Optional[models.Admin]
) -> None:
    """保存文章历史版本"""
    if not post_obj:
        return
    revision = models.PostRevision(
        post_id=post_obj.id,
        title=post_obj.title,
        slug=post_obj.slug,
        description=post_obj.description,
        content=post_obj.content,
        editor=getattr(editor, "username", None)
    )
    db.add(revision)
    db.commit()


# ============== 数据模型 ==============

class TagBase(BaseModel):
    """标签基础模型"""
    name: str = Field(..., description="标签名称")


class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str = Field(..., description="分类名称")


class PostBase(BaseModel):
    """
    文章请求模型

    用于创建和更新文章时的请求体
    """
    title: str = Field(..., description="文章标题")
    slug: str = Field(..., description="文章 URL 别名")
    description: str = Field(default="", description="文章摘要描述")
    content: str = Field(..., description="文章正文内容（Markdown 格式）")
    image: str = Field(default="", description="封面图片 URL")
    category_name: str = Field(..., description="分类名称")
    tags: List[str] = Field(default=[], description="标签列表")
    password: str = Field(default="", description="文章访问密码（可选）")
    is_draft: bool = Field(default=False, description="是否为草稿")
    pinned: bool = Field(default=False, description="是否置顶")
    pin_order: int = Field(default=0, description="置顶排序（数字越小越靠前）")
    status: Optional[str] = Field(default=None, description="发布状态")
    scheduled_at: Optional[datetime] = Field(default=None, description="定时发布时间")
    published_at: Optional[datetime] = Field(default=None, description="自定义发布时间")


class PostResponse(BaseModel):
    """文章响应模型"""
    id: str = Field(..., description="文章 UUID")
    title: str = Field(..., description="文章标题")
    slug: str = Field(..., description="文章 URL 别名")
    description: Optional[str] = Field(None, description="文章摘要")
    content: str = Field(..., description="文章内容")
    image: Optional[str] = Field(None, description="封面图片")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    category: Optional[str] = Field(None, description="分类名称")
    tags: List[str] = Field(default=[], description="标签列表")
    is_draft: bool = Field(..., description="是否为草稿")
    pinned: bool = Field(default=False, description="是否置顶")
    pin_order: int = Field(default=0, description="置顶排序")
    has_password: bool = Field(..., description="是否有密码保护")
    status: str = Field(default="draft", description="发布状态")
    scheduled_at: Optional[datetime] = Field(default=None, description="定时发布时间")
    autosave_available: bool = Field(default=False, description="是否存在自动保存内容")


class PostAutosaveRequest(BaseModel):
    """自动保存请求模型"""
    title: str = Field(default="", description="文章标题")
    slug: str = Field(default="", description="文章别名")
    description: Optional[str] = Field(default="", description="摘要")
    content: str = Field(..., description="正文内容")
    category_name: Optional[str] = Field(default=None, description="分类名称")
    tags: List[str] = Field(default=[], description="标签")
    image: Optional[str] = Field(default=None, description="封面图")
    password: Optional[str] = Field(default="", description="密码")
    pinned: Optional[bool] = Field(default=False, description="是否置顶")
    pin_order: Optional[int] = Field(default=0, description="置顶排序")


class AutosaveResponse(BaseModel):
    """自动保存响应模型"""
    saved_at: Optional[datetime]
    data: Optional[dict]


class RevisionResponse(BaseModel):
    """版本记录响应模型"""
    id: str
    title: str
    slug: str
    editor: Optional[str]
    created_at: datetime


# ============== API 接口 ==============

@router.get("", response_model=List[dict], summary="获取文章列表")
def get_posts(
    page: int = 1,
    page_size: int = 10,
    all: bool = False,
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    """
    获取所有文章列表

    公开接口，无需认证。返回文章基本信息，不包含密码等敏感字段。
    文章按置顶优先、置顶排序、发布时间倒序排列。

    Args:
        page: 页码，从1开始，默认为1
        page_size: 每页数量，默认为10
        all: 是否返回全部文章（不分页），默认为False
        include_deleted: 是否包含已删除的文章，默认为False

    Returns:
        List[dict]: 文章列表，包含分页信息
    """
    # 自动发布已到时间的定时文章
    process_scheduled_posts(db)

    # 按置顶优先、置顶排序（数字小的在前）、发布时间倒序排列
    query = db.query(models.Post)

    # 默认不包含已删除的文章
    if not include_deleted:
        query = query.filter(models.Post.deleted_at == None)

    query = query.order_by(
        models.Post.pinned.desc(),
        models.Post.pin_order.asc(),
        models.Post.published_at.desc()
    )

    # 获取总数
    total = query.count()

    # 如果不是获取全部，则分页
    if not all:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    posts = query.all()

    return [{
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "description": p.description,
        "content": p.content,
        "image": p.image,
        "published_at": p.published_at,
        "category": p.category.name if p.category else None,
        "tags": [t.name for t in p.tags],
        "is_draft": p.is_draft == 1,
        "pinned": p.pinned or False,
        "pin_order": p.pin_order or 0,
        "has_password": p.password is not None and p.password != "",
        "status": p.status or ("draft" if p.is_draft else "published"),
        "scheduled_at": p.scheduled_at,
        "autosave_available": bool(p.autosave_data),
        "deleted_at": p.deleted_at,
        "_pagination": {
            "page": page if not all else 1,
            "page_size": page_size if not all else total,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if not all else 1
        }
    } for p in posts]


@router.get("/{post_id}", response_model=dict, summary="获取单篇文章")
def get_post(post_id: str, db: Session = Depends(get_db)):
    """
    根据 ID 获取单篇文章详情

    公开接口，无需认证。

    Args:
        post_id: 文章 UUID

    Returns:
        dict: 文章详情

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    process_scheduled_posts(db)
    p = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="文章不存在")

    return {
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "description": p.description,
        "content": p.content,
        "image": p.image,
        "published_at": p.published_at,
        "category": p.category.name if p.category else None,
        "tags": [t.name for t in p.tags],
        "is_draft": p.is_draft == 1,
        "pinned": p.pinned or False,
        "pin_order": p.pin_order or 0,
        "password": p.password,
        "status": p.status or ("draft" if p.is_draft else "published"),
        "scheduled_at": p.scheduled_at,
        "autosave_available": bool(p.autosave_data)
    }


@router.get("/slug/{slug}", response_model=dict, summary="通过 Slug 获取文章")
def get_post_by_slug(slug: str, db: Session = Depends(get_db)):
    """
    根据 Slug 获取单篇文章详情

    公开接口，无需认证。

    Args:
        slug: 文章 URL 别名

    Returns:
        dict: 文章详情

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    process_scheduled_posts(db)
    p = db.query(models.Post).filter(models.Post.slug == slug).first()
    if not p:
        raise HTTPException(status_code=404, detail="文章不存在")

    return {
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "description": p.description,
        "content": p.content,
        "image": p.image,
        "published_at": p.published_at,
        "category": p.category.name if p.category else None,
        "tags": [t.name for t in p.tags],
        "is_draft": p.is_draft == 1,
        "pinned": p.pinned or False,
        "pin_order": p.pin_order or 0,
        "password": p.password,
        "status": p.status or ("draft" if p.is_draft else "published"),
        "scheduled_at": p.scheduled_at,
        "autosave_available": bool(p.autosave_data)
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="创建文章")
def create_post(
        post: PostBase,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    创建新文章

    需要认证。如果分类或标签不存在，会自动创建。

    Args:
        post: 文章数据

    Returns:
        dict: 包含成功消息和新文章 ID
    """
    # 获取或创建分类
    db_category = db.query(models.Category).filter(
        models.Category.name == post.category_name
    ).first()

    if not db_category:
        db_category = models.Category(name=post.category_name)
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

    status = normalize_status(post.status, post.is_draft)
    scheduled_at = normalize_datetime(post.scheduled_at)
    published_at = normalize_datetime(post.published_at)

    if status == "scheduled" and not scheduled_at:
        raise HTTPException(status_code=400, detail="定时发布必须设置发布时间")

    if status == "published":
        if not published_at:
            published_at = datetime.utcnow()
    elif status == "scheduled":
        if not published_at:
            published_at = scheduled_at
    else:
        if not published_at:
            published_at = datetime.utcnow()

    # 创建文章
    # 如果设置了密码，进行哈希处理
    hashed_password = auth.get_password_hash(post.password) if post.password else None

    db_post = models.Post(
        title=post.title,
        slug=post.slug,
        description=post.description,
        content=post.content,
        image=post.image if post.image else None,
        category_id=db_category.id,
        password=hashed_password,
        is_draft=0 if status == "published" else 1,
        status=status,
        scheduled_at=scheduled_at,
        published_at=published_at,
        pinned=post.pinned,
        pin_order=post.pin_order
    )

    # 处理标签
    for tag_name in post.tags:
        db_tag = db.query(models.Tag).filter(
            models.Tag.name == tag_name
        ).first()

        if not db_tag:
            db_tag = models.Tag(name=tag_name)
            db.add(db_tag)
            db.commit()
            db.refresh(db_tag)

        db_post.tags.append(db_tag)

    # 保存文章
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    create_revision_snapshot(db, db_post, current_user)
    sync_post_media(db, db_post.id, db_post.content, db_post.image)
    invalidate_posts_cache()

    return {"message": "文章创建成功", "id": db_post.id}


@router.put("/{post_id}", summary="更新文章")
def update_post(
        post_id: str,
        post: PostBase,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    更新指定文章

    需要认证。

    Args:
        post_id: 文章 UUID
        post: 更新的文章数据

    Returns:
        dict: 成功消息

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    # 查找文章
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 获取或创建分类
    db_category = db.query(models.Category).filter(
        models.Category.name == post.category_name
    ).first()

    if not db_category:
        db_category = models.Category(name=post.category_name)
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

    status = normalize_status(post.status, post.is_draft)
    scheduled_at = normalize_datetime(post.scheduled_at)
    published_at = normalize_datetime(post.published_at)

    if status == "scheduled" and not scheduled_at:
        raise HTTPException(status_code=400, detail="定时发布必须设置发布时间")

    if status == "published" and not published_at:
        published_at = datetime.utcnow()
    elif status == "scheduled" and not published_at:
        published_at = scheduled_at

    # 更新文章字段
    db_post.title = post.title
    db_post.slug = post.slug
    db_post.description = post.description
    db_post.content = post.content
    db_post.image = post.image if post.image else None
    db_post.category_id = db_category.id
    # 如果设置了新密码，进行哈希处理；如果清空密码，则设为 None
    if post.password:
        db_post.password = auth.get_password_hash(post.password)
    elif post.password == "":
        db_post.password = None
    # 如果 password 字段未提供（None），保持原密码不变
    db_post.is_draft = 0 if status == "published" else 1
    db_post.pinned = post.pinned
    db_post.pin_order = post.pin_order
    db_post.status = status
    db_post.scheduled_at = scheduled_at if status == "scheduled" else None
    if published_at:
        db_post.published_at = published_at
    elif db_post.published_at is None:
        db_post.published_at = datetime.utcnow()

    # 更新标签（先清空再添加）
    db_post.tags = []
    for tag_name in post.tags:
        db_tag = db.query(models.Tag).filter(
            models.Tag.name == tag_name
        ).first()

        if not db_tag:
            db_tag = models.Tag(name=tag_name)
            db.add(db_tag)
            db.commit()
            db.refresh(db_tag)

        db_post.tags.append(db_tag)

    db.commit()
    create_revision_snapshot(db, db_post, current_user)
    sync_post_media(db, db_post.id, db_post.content, db_post.image)
    invalidate_posts_cache()
    return {"message": "文章更新成功"}


@router.delete("/{post_id}", summary="删除文章（软删除）")
def delete_post(
        post_id: str,
        permanent: bool = False,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    删除指定文章（软删除）

    需要认证。默认为软删除，文章会移入回收站。
    如果 permanent=True，则永久删除文章。

    Args:
        post_id: 文章 UUID
        permanent: 是否永久删除，默认为 False（软删除）

    Returns:
        dict: 成功消息

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    if permanent:
        # 永久删除
        media_ids = [media.id for media in db_post.media_files]
        db.query(models.PostMedia).filter(
            models.PostMedia.post_id == post_id
        ).delete(synchronize_session=False)
        db.delete(db_post)
        db.commit()
        refresh_media_usage_counts(db, media_ids)
        db.commit()
        invalidate_posts_cache()
        return {"message": "文章已永久删除"}
    else:
        # 软删除
        db_post.deleted_at = datetime.utcnow()
        db.commit()
        invalidate_posts_cache()
        return {"message": "文章已移入回收站"}


@router.get("/scheduled/queue", summary="获取定时发布队列")
def get_scheduled_queue(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """获取待发布的定时文章列表"""
    query = db.query(models.Post).filter(
        models.Post.status == "scheduled",
        models.Post.scheduled_at != None
    ).order_by(models.Post.scheduled_at.asc())

    total = query.count()
    posts = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for post in posts:
        attempts = db.query(models.ScheduledPublishLog).filter(
            models.ScheduledPublishLog.post_id == post.id
        ).count()
        last_log = db.query(models.ScheduledPublishLog).filter(
            models.ScheduledPublishLog.post_id == post.id
        ).order_by(models.ScheduledPublishLog.created_at.desc()).first()

        items.append({
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "scheduled_at": post.scheduled_at,
            "status": "failed" if last_log and last_log.status == "failed" else "pending",
            "attempts": attempts,
            "last_attempt_at": last_log.created_at if last_log else None,
            "last_error": last_log.message if last_log and last_log.status == "failed" else None
        })

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/scheduled/logs", summary="获取定时发布日志")
def get_scheduled_logs(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """获取定时发布日志"""
    query = db.query(models.ScheduledPublishLog).order_by(
        models.ScheduledPublishLog.created_at.desc()
    )
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [{
            "id": log.id,
            "post_id": log.post_id,
            "post_title": log.post.title if log.post else "",
            "slug": log.post.slug if log.post else "",
            "status": log.status,
            "message": log.message,
            "scheduled_at": log.scheduled_at,
            "created_at": log.created_at
        } for log in logs],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.post("/{post_id}/scheduled/retry", summary="手动重试定时发布")
def retry_scheduled_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """手动重试定时发布"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    if db_post.status != "scheduled":
        raise HTTPException(status_code=400, detail="文章不在定时发布状态")

    db_post.scheduled_at = datetime.utcnow()
    db_post.is_draft = 0
    db.commit()
    return {"message": "已加入发布队列"}


@router.patch("/{post_id}/pin", summary="切换文章置顶状态")
def toggle_post_pin(
        post_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    切换文章的置顶状态

    需要认证。如果文章当前是置顶状态，则取消置顶；否则设为置顶。

    Args:
        post_id: 文章 UUID

    Returns:
        dict: 包含成功消息和新的置顶状态

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 切换置顶状态
    db_post.pinned = not (db_post.pinned or False)
    db.commit()
    invalidate_posts_cache()

    return {
        "message": "置顶" if db_post.pinned else "取消置顶" + "成功",
        "pinned": db_post.pinned
    }


@router.put("/{post_id}/pin", summary="设置文章置顶状态")
def set_post_pin(
        post_id: str,
        pinned: bool,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    设置文章的置顶状态

    需要认证。

    Args:
        post_id: 文章 UUID
        pinned: 是否置顶

    Returns:
        dict: 成功消息

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    db_post.pinned = pinned
    db.commit()
    invalidate_posts_cache()

    return {
        "message": "置顶状态更新成功",
        "pinned": db_post.pinned
    }


class PasswordVerifyRequest(BaseModel):
    """密码验证请求模型"""
    password: str = Field(..., description="用户输入的密码")


@router.post("/{post_id}/verify-password", summary="验证文章密码")
def verify_post_password(
        post_id: str,
        request: PasswordVerifyRequest,
        db: Session = Depends(get_db)
):
    """
    验证文章访问密码

    公开接口，无需认证。用于前端验证用户输入的密码是否正确。

    Args:
        post_id: 文章 UUID
        request: 包含用户输入密码的请求体

    Returns:
        dict: 验证结果，包含 valid 字段表示密码是否正确

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 如果文章没有密码保护
    if not db_post.password:
        return {"valid": True, "message": "文章无密码保护"}

    # 验证密码
    is_valid = auth.verify_password(request.password, db_post.password)

    if is_valid:
        return {"valid": True, "message": "密码正确"}
    else:
        return {"valid": False, "message": "密码错误"}


@router.post("/{post_id}/autosave", summary="自动保存文章内容")
def autosave_post(
        post_id: str,
        autosave: PostAutosaveRequest,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """自动保存文章草稿，避免内容丢失"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    db_post.autosave_data = json.dumps(autosave.model_dump(), ensure_ascii=False)
    db_post.autosave_at = datetime.utcnow()
    db.commit()
    return {
        "message": "自动保存成功",
        "saved_at": db_post.autosave_at
    }


@router.get("/{post_id}/autosave", response_model=AutosaveResponse, summary="获取自动保存内容")
def get_autosave_post(
        post_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """获取文章的自动保存内容"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    if not db_post.autosave_data:
        return {"saved_at": None, "data": None}

    return {
        "saved_at": db_post.autosave_at,
        "data": json.loads(db_post.autosave_data)
    }


@router.delete("/{post_id}/autosave", summary="删除自动保存内容")
def delete_autosave_post(
        post_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """清除文章的自动保存内容"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    db_post.autosave_data = None
    db_post.autosave_at = None
    db.commit()
    return {"message": "自动保存内容已清除"}


@router.get("/{post_id}/revisions", response_model=List[RevisionResponse], summary="获取文章历史版本")
def get_post_revisions(
        post_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """列出文章的历史版本"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    revisions = db.query(models.PostRevision).filter(
        models.PostRevision.post_id == post_id
    ).order_by(models.PostRevision.created_at.desc()).limit(20).all()

    return [{
        "id": rev.id,
        "title": rev.title,
        "slug": rev.slug,
        "editor": rev.editor,
        "created_at": rev.created_at
    } for rev in revisions]


@router.post("/{post_id}/revisions/{revision_id}/restore", summary="恢复文章到指定版本")
def restore_post_revision(
        post_id: str,
        revision_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """将文章内容恢复到历史版本"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    revision = db.query(models.PostRevision).filter(
        models.PostRevision.id == revision_id,
        models.PostRevision.post_id == post_id
    ).first()
    if not revision:
        raise HTTPException(status_code=404, detail="版本不存在")

    db_post.title = revision.title
    db_post.slug = revision.slug
    db_post.description = revision.description
    db_post.content = revision.content
    db_post.autosave_data = None
    db_post.autosave_at = None
    db.commit()
    create_revision_snapshot(db, db_post, current_user)
    return {"message": "文章已恢复到指定版本"}


@router.delete("/{post_id}/revisions/{revision_id}", summary="删除文章历史版本")
def delete_post_revision(
        post_id: str,
        revision_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """删除指定文章的历史版本"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    revision = db.query(models.PostRevision).filter(
        models.PostRevision.id == revision_id,
        models.PostRevision.post_id == post_id
    ).first()
    if not revision:
        raise HTTPException(status_code=404, detail="版本不存在")

    db.delete(revision)
    db.commit()
    return {"message": "版本已删除"}


# ============== 回收站相关 API ==============

@router.get("/trash/list", response_model=List[dict], summary="获取回收站文章列表")
def get_trash_posts(
    page: int = 1,
    page_size: int = 10,
    all: bool = False,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    获取回收站中的文章列表

    需要认证。只返回已软删除的文章。

    Args:
        page: 页码，从1开始，默认为1
        page_size: 每页数量，默认为10
        all: 是否返回全部文章（不分页），默认为False

    Returns:
        List[dict]: 回收站文章列表
    """
    process_scheduled_posts(db)
    # 只查询已删除的文章，按删除时间倒序排列
    query = db.query(models.Post).filter(
        models.Post.deleted_at != None
    ).order_by(models.Post.deleted_at.desc())

    # 获取总数
    total = query.count()

    # 如果不是获取全部，则分页
    if not all:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    posts = query.all()

    return [{
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "description": p.description,
        "image": p.image,
        "published_at": p.published_at,
        "deleted_at": p.deleted_at,
        "category": p.category.name if p.category else None,
        "tags": [t.name for t in p.tags],
        "is_draft": p.is_draft == 1,
        "status": p.status or ("draft" if p.is_draft else "published"),
        "scheduled_at": p.scheduled_at,
        "_pagination": {
            "page": page if not all else 1,
            "page_size": page_size if not all else total,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if not all else 1
        }
    } for p in posts]


@router.post("/{post_id}/restore", summary="恢复已删除的文章")
def restore_post(
        post_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    从回收站恢复文章

    需要认证。

    Args:
        post_id: 文章 UUID

    Returns:
        dict: 成功消息

    Raises:
        HTTPException: 文章不存在或未被删除时返回错误
    """
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    if db_post.deleted_at is None:
        raise HTTPException(status_code=400, detail="文章未被删除，无需恢复")

    # 恢复文章
    db_post.deleted_at = None
    db.commit()
    invalidate_posts_cache()

    return {"message": "文章已恢复"}


@router.delete("/trash/empty", summary="清空回收站")
def empty_trash(
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    清空回收站（永久删除所有已软删除的文章）

    需要认证。此操作不可逆。

    Returns:
        dict: 成功消息，包含删除的文章数量
    """
    # 查询所有已删除的文章
    deleted_posts = db.query(models.Post).filter(
        models.Post.deleted_at != None
    ).all()

    count = len(deleted_posts)

    # 永久删除
    for post in deleted_posts:
        db.delete(post)

    db.commit()
    invalidate_posts_cache()

    return {"message": f"已永久删除 {count} 篇文章"}

