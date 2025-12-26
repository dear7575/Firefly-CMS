"""
仪表盘路由模块
提供统计数据 API 接口
"""
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from database import get_db

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/stats", summary="获取仪表盘统计数据")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取仪表盘统计数据"""

    # 文章统计
    total_posts = db.query(func.count(models.Post.id)).scalar()
    published_posts = db.query(func.count(models.Post.id)).filter(
        models.Post.is_draft == 0
    ).scalar()
    draft_posts = db.query(func.count(models.Post.id)).filter(
        models.Post.is_draft == 1
    ).scalar()

    # 分类统计
    total_categories = db.query(func.count(models.Category.id)).scalar()

    # 标签统计
    total_tags = db.query(func.count(models.Tag.id)).scalar()

    # 友链统计
    total_friends = db.query(func.count(models.FriendLink.id)).scalar()
    enabled_friends = db.query(func.count(models.FriendLink.id)).filter(
        models.FriendLink.enabled == True
    ).scalar()

    # 最近7天发布的文章数
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_posts = db.query(func.count(models.Post.id)).filter(
        models.Post.published_at >= seven_days_ago,
        models.Post.is_draft == 0
    ).scalar()

    # 最近发布的5篇文章
    latest_posts = db.query(models.Post).filter(
        models.Post.is_draft == 0
    ).order_by(models.Post.published_at.desc()).limit(5).all()

    latest_posts_data = [{
        "id": p.id,
        "title": p.title,
        "slug": p.slug,
        "published_at": p.published_at,
        "category": p.category.name if p.category else None
    } for p in latest_posts]

    # 各分类文章数统计
    category_stats = db.query(
        models.Category.name,
        func.count(models.Post.id).label('count')
    ).outerjoin(models.Post).group_by(models.Category.id).all()

    category_data = [{"name": c[0], "count": c[1]} for c in category_stats]

    return {
        "posts": {
            "total": total_posts,
            "published": published_posts,
            "draft": draft_posts,
            "recent": recent_posts
        },
        "categories": {
            "total": total_categories,
            "stats": category_data
        },
        "tags": {
            "total": total_tags
        },
        "friends": {
            "total": total_friends,
            "enabled": enabled_friends
        },
        "latest_posts": latest_posts_data
    }
