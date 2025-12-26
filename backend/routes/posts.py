"""
文章路由模块
提供文章的增删改查 API 接口（含置顶功能）
"""
from datetime import datetime
from typing import List, Optional

import models
import auth
from database import get_db, settings
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# 创建路由器
router = APIRouter(prefix="/posts", tags=["文章管理"])

# OAuth2 密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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


class PostResponse(BaseModel):
    """文章响应模型"""
    id: str = Field(..., description="文章 UUID")
    title: str = Field(..., description="文章标题")
    slug: str = Field(..., description="文章 URL 别名")
    description: Optional[str] = Field(None, description="文章摘要")
    content: str = Field(..., description="文章内容")
    image: Optional[str] = Field(None, description="封面图片")
    published_at: datetime = Field(..., description="发布时间")
    category: Optional[str] = Field(None, description="分类名称")
    tags: List[str] = Field(default=[], description="标签列表")
    is_draft: bool = Field(..., description="是否为草稿")
    pinned: bool = Field(default=False, description="是否置顶")
    pin_order: int = Field(default=0, description="置顶排序")
    has_password: bool = Field(..., description="是否有密码保护")


# ============== API 接口 ==============

@router.get("", response_model=List[dict], summary="获取文章列表")
def get_posts(
    page: int = 1,
    page_size: int = 10,
    all: bool = False,
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

    Returns:
        List[dict]: 文章列表，包含分页信息
    """
    # 按置顶优先、置顶排序（数字小的在前）、发布时间倒序排列
    query = db.query(models.Post).order_by(
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
        "password": p.password
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
        is_draft=1 if post.is_draft else 0,
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
    db_post.is_draft = 1 if post.is_draft else 0
    db_post.pinned = post.pinned
    db_post.pin_order = post.pin_order

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
    return {"message": "文章更新成功"}


@router.delete("/{post_id}", summary="删除文章")
def delete_post(
        post_id: str,
        db: Session = Depends(get_db),
        current_user: models.Admin = Depends(get_current_user)
):
    """
    删除指定文章

    需要认证。

    Args:
        post_id: 文章 UUID

    Returns:
        dict: 成功消息

    Raises:
        HTTPException: 文章不存在时返回 404
    """
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(db_post)
    db.commit()
    return {"message": "文章删除成功"}


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

