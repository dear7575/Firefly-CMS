"""
数据备份与恢复路由模块
提供数据导出和导入功能
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import io

import models
from database import get_db, settings

router = APIRouter(prefix="/backup", tags=["数据备份"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """验证 JWT Token 并获取当前用户"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.Admin).filter(models.Admin.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/export", summary="导出所有数据")
async def export_data(
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    导出所有博客数据为 JSON 格式

    需要认证。导出内容包括：
    - 文章（不含密码）
    - 分类
    - 标签
    - 友链
    - 社交链接
    - 站点设置

    Returns:
        StreamingResponse: JSON 文件下载
    """
    # 导出文章
    posts = db.query(models.Post).all()
    posts_data = [{
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "description": p.description,
        "content": p.content,
        "image": p.image,
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "category_name": p.category.name if p.category else None,
        "tags": [t.name for t in p.tags],
        "is_draft": p.is_draft == 1,
        "pinned": p.pinned or False,
        "pin_order": p.pin_order or 0,
        "has_password": p.password is not None and p.password != ""
    } for p in posts]

    # 导出分类
    categories = db.query(models.Category).all()
    categories_data = [{
        "id": c.id,
        "name": c.name,
        "slug": c.slug,
        "description": c.description,
        "icon": c.icon,
        "color": c.color,
        "sort_order": c.sort_order,
        "enabled": c.enabled
    } for c in categories]

    # 导出标签
    tags = db.query(models.Tag).all()
    tags_data = [{
        "id": t.id,
        "name": t.name,
        "slug": t.slug,
        "color": t.color,
        "enabled": t.enabled
    } for t in tags]

    # 导出友链
    friends = db.query(models.FriendLink).all()
    friends_data = [{
        "id": f.id,
        "title": f.title,
        "url": f.url,
        "avatar": f.avatar,
        "description": f.description,
        "tags": f.tags,
        "weight": f.weight,
        "enabled": f.enabled
    } for f in friends]

    # 导出社交链接
    socials = db.query(models.SocialLink).all()
    socials_data = [{
        "id": s.id,
        "name": s.name,
        "icon": s.icon,
        "url": s.url,
        "show_name": s.show_name,
        "sort_order": s.sort_order,
        "enabled": s.enabled
    } for s in socials]

    # 导出站点设置
    site_settings = db.query(models.SiteSetting).all()
    settings_data = [{
        "key": s.key,
        "value": s.value,
        "type": s.type,
        "group": s.group,
        "label": s.label,
        "description": s.description
    } for s in site_settings]

    # 组装导出数据
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "data": {
            "posts": posts_data,
            "categories": categories_data,
            "tags": tags_data,
            "friends": friends_data,
            "socials": socials_data,
            "settings": settings_data
        },
        "stats": {
            "posts": len(posts_data),
            "categories": len(categories_data),
            "tags": len(tags_data),
            "friends": len(friends_data),
            "socials": len(socials_data),
            "settings": len(settings_data)
        }
    }

    # 生成 JSON 文件
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"firefly_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return StreamingResponse(
        io.BytesIO(json_str.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/posts", summary="仅导出文章")
async def export_posts(
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """仅导出文章数据"""
    posts = db.query(models.Post).all()
    posts_data = [{
        "title": p.title,
        "slug": p.slug,
        "description": p.description,
        "content": p.content,
        "image": p.image,
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "category_name": p.category.name if p.category else None,
        "tags": [t.name for t in p.tags],
        "is_draft": p.is_draft == 1,
        "pinned": p.pinned or False,
        "pin_order": p.pin_order or 0
    } for p in posts]

    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "type": "posts",
        "data": posts_data,
        "count": len(posts_data)
    }

    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"firefly_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return StreamingResponse(
        io.BytesIO(json_str.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/import", summary="导入数据")
async def import_data(
    file: UploadFile = File(...),
    merge: bool = False,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    从 JSON 文件导入数据

    需要认证。

    Args:
        file: JSON 备份文件
        merge: 是否合并数据（True: 合并，False: 覆盖）

    Returns:
        dict: 导入结果统计
    """
    # 读取并解析 JSON
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")

    # 验证数据格式
    if "data" not in data:
        raise HTTPException(status_code=400, detail="无效的备份文件格式")

    import_stats = {
        "posts": {"imported": 0, "skipped": 0, "errors": 0},
        "categories": {"imported": 0, "skipped": 0, "errors": 0},
        "tags": {"imported": 0, "skipped": 0, "errors": 0},
        "friends": {"imported": 0, "skipped": 0, "errors": 0},
        "socials": {"imported": 0, "skipped": 0, "errors": 0},
        "settings": {"imported": 0, "skipped": 0, "errors": 0}
    }

    backup_data = data["data"]

    # 导入分类
    if "categories" in backup_data:
        for cat_data in backup_data["categories"]:
            try:
                existing = db.query(models.Category).filter(
                    models.Category.name == cat_data["name"]
                ).first()

                if existing:
                    if merge:
                        import_stats["categories"]["skipped"] += 1
                        continue
                    else:
                        # 更新现有分类
                        existing.slug = cat_data.get("slug")
                        existing.description = cat_data.get("description")
                        existing.icon = cat_data.get("icon")
                        existing.color = cat_data.get("color")
                        existing.sort_order = cat_data.get("sort_order", 0)
                        existing.enabled = cat_data.get("enabled", True)
                else:
                    new_cat = models.Category(
                        name=cat_data["name"],
                        slug=cat_data.get("slug"),
                        description=cat_data.get("description"),
                        icon=cat_data.get("icon"),
                        color=cat_data.get("color"),
                        sort_order=cat_data.get("sort_order", 0),
                        enabled=cat_data.get("enabled", True)
                    )
                    db.add(new_cat)

                import_stats["categories"]["imported"] += 1
            except Exception as e:
                import_stats["categories"]["errors"] += 1

    # 导入标签
    if "tags" in backup_data:
        for tag_data in backup_data["tags"]:
            try:
                existing = db.query(models.Tag).filter(
                    models.Tag.name == tag_data["name"]
                ).first()

                if existing:
                    if merge:
                        import_stats["tags"]["skipped"] += 1
                        continue
                    else:
                        existing.slug = tag_data.get("slug")
                        existing.color = tag_data.get("color")
                        existing.enabled = tag_data.get("enabled", True)
                else:
                    new_tag = models.Tag(
                        name=tag_data["name"],
                        slug=tag_data.get("slug"),
                        color=tag_data.get("color"),
                        enabled=tag_data.get("enabled", True)
                    )
                    db.add(new_tag)

                import_stats["tags"]["imported"] += 1
            except Exception as e:
                import_stats["tags"]["errors"] += 1

    db.commit()

    # 导入文章
    if "posts" in backup_data:
        for post_data in backup_data["posts"]:
            try:
                existing = db.query(models.Post).filter(
                    models.Post.slug == post_data["slug"]
                ).first()

                if existing:
                    if merge:
                        import_stats["posts"]["skipped"] += 1
                        continue
                    else:
                        # 更新现有文章
                        existing.title = post_data["title"]
                        existing.description = post_data.get("description")
                        existing.content = post_data["content"]
                        existing.image = post_data.get("image")
                        existing.is_draft = 1 if post_data.get("is_draft") else 0
                        existing.pinned = post_data.get("pinned", False)
                        existing.pin_order = post_data.get("pin_order", 0)

                        # 更新分类
                        if post_data.get("category_name"):
                            cat = db.query(models.Category).filter(
                                models.Category.name == post_data["category_name"]
                            ).first()
                            if cat:
                                existing.category_id = cat.id

                        # 更新标签
                        existing.tags = []
                        for tag_name in post_data.get("tags", []):
                            tag = db.query(models.Tag).filter(
                                models.Tag.name == tag_name
                            ).first()
                            if tag:
                                existing.tags.append(tag)
                else:
                    # 获取分类
                    category_id = None
                    if post_data.get("category_name"):
                        cat = db.query(models.Category).filter(
                            models.Category.name == post_data["category_name"]
                        ).first()
                        if cat:
                            category_id = cat.id

                    new_post = models.Post(
                        title=post_data["title"],
                        slug=post_data["slug"],
                        description=post_data.get("description"),
                        content=post_data["content"],
                        image=post_data.get("image"),
                        category_id=category_id,
                        is_draft=1 if post_data.get("is_draft") else 0,
                        pinned=post_data.get("pinned", False),
                        pin_order=post_data.get("pin_order", 0)
                    )

                    # 添加标签
                    for tag_name in post_data.get("tags", []):
                        tag = db.query(models.Tag).filter(
                            models.Tag.name == tag_name
                        ).first()
                        if tag:
                            new_post.tags.append(tag)

                    db.add(new_post)

                import_stats["posts"]["imported"] += 1
            except Exception as e:
                import_stats["posts"]["errors"] += 1

    # 导入友链
    if "friends" in backup_data:
        for friend_data in backup_data["friends"]:
            try:
                existing = db.query(models.FriendLink).filter(
                    models.FriendLink.url == friend_data["url"]
                ).first()

                if existing:
                    if merge:
                        import_stats["friends"]["skipped"] += 1
                        continue
                    else:
                        existing.title = friend_data["title"]
                        existing.avatar = friend_data.get("avatar")
                        existing.description = friend_data.get("description")
                        existing.tags = friend_data.get("tags")
                        existing.weight = friend_data.get("weight", 0)
                        existing.enabled = friend_data.get("enabled", True)
                else:
                    new_friend = models.FriendLink(
                        title=friend_data["title"],
                        url=friend_data["url"],
                        avatar=friend_data.get("avatar"),
                        description=friend_data.get("description"),
                        tags=friend_data.get("tags"),
                        weight=friend_data.get("weight", 0),
                        enabled=friend_data.get("enabled", True)
                    )
                    db.add(new_friend)

                import_stats["friends"]["imported"] += 1
            except Exception as e:
                import_stats["friends"]["errors"] += 1

    # 导入站点设置
    if "settings" in backup_data:
        for setting_data in backup_data["settings"]:
            try:
                existing = db.query(models.SiteSetting).filter(
                    models.SiteSetting.key == setting_data["key"]
                ).first()

                if existing:
                    if not merge:
                        existing.value = setting_data.get("value")
                        existing.type = setting_data.get("type", "string")
                        existing.group = setting_data.get("group", "general")
                        import_stats["settings"]["imported"] += 1
                    else:
                        import_stats["settings"]["skipped"] += 1
                else:
                    new_setting = models.SiteSetting(
                        key=setting_data["key"],
                        value=setting_data.get("value"),
                        type=setting_data.get("type", "string"),
                        group=setting_data.get("group", "general"),
                        label=setting_data.get("label"),
                        description=setting_data.get("description")
                    )
                    db.add(new_setting)
                    import_stats["settings"]["imported"] += 1
            except Exception as e:
                import_stats["settings"]["errors"] += 1

    db.commit()

    return {
        "message": "数据导入完成",
        "stats": import_stats
    }
