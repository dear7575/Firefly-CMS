"""
仪表盘路由模块
提供统计数据 API 接口
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

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
    # 加密文章统计（有密码的文章）
    encrypted_posts = db.query(func.count(models.Post.id)).filter(
        models.Post.password != None,
        models.Post.password != ""
    ).scalar()
    # 置顶文章统计
    pinned_posts = db.query(func.count(models.Post.id)).filter(
        models.Post.pinned == True
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

    # 最近30天每日发布统计
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_posts = db.query(
        func.date(models.Post.published_at).label('date'),
        func.count(models.Post.id).label('count')
    ).filter(
        models.Post.published_at >= thirty_days_ago,
        models.Post.is_draft == 0
    ).group_by(func.date(models.Post.published_at)).all()

    # 填充缺失的日期
    daily_data = defaultdict(int)
    for row in daily_posts:
        daily_data[str(row.date)] = row.count

    daily_stats = []
    for i in range(30):
        date = (datetime.utcnow() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        daily_stats.append({"date": date, "count": daily_data.get(date, 0)})

    # 月度发布统计（最近12个月）
    monthly_posts = db.query(
        extract('year', models.Post.published_at).label('year'),
        extract('month', models.Post.published_at).label('month'),
        func.count(models.Post.id).label('count')
    ).filter(
        models.Post.is_draft == 0
    ).group_by(
        extract('year', models.Post.published_at),
        extract('month', models.Post.published_at)
    ).order_by(
        extract('year', models.Post.published_at).desc(),
        extract('month', models.Post.published_at).desc()
    ).limit(12).all()

    monthly_stats = [{
        "year": int(m.year),
        "month": int(m.month),
        "count": m.count
    } for m in reversed(monthly_posts)]

    # 标签使用统计（Top 10）
    tag_stats = db.query(
        models.Tag.name,
        func.count(models.post_tags.c.post_id).label('count')
    ).join(models.post_tags).group_by(models.Tag.id).order_by(
        func.count(models.post_tags.c.post_id).desc()
    ).limit(10).all()

    tag_data = [{"name": t[0], "count": t[1]} for t in tag_stats]

    # 登录日志统计（最近7天）
    login_stats = db.query(
        func.date(models.AccessLog.created_at).label('date'),
        models.AccessLog.log_type,
        func.count(models.AccessLog.id).label('count')
    ).filter(
        models.AccessLog.created_at >= seven_days_ago,
        models.AccessLog.log_type.in_(['login_success', 'login_failed'])
    ).group_by(
        func.date(models.AccessLog.created_at),
        models.AccessLog.log_type
    ).all()

    login_data = defaultdict(lambda: {"success": 0, "failed": 0})
    for row in login_stats:
        if row.log_type == 'login_success':
            login_data[str(row.date)]["success"] = row.count
        else:
            login_data[str(row.date)]["failed"] = row.count

    login_stats_list = []
    for i in range(7):
        date_str = (datetime.utcnow() - timedelta(days=6-i)).strftime('%Y-%m-%d')
        login_stats_list.append({
            "date": date_str,
            "success": login_data[date_str]["success"],
            "failed": login_data[date_str]["failed"]
        })

    # 阅读统计
    total_views = db.query(func.coalesce(func.sum(models.PostViewStat.views), 0)).scalar() or 0
    view_stats = db.query(
        models.PostViewStat.date,
        func.sum(models.PostViewStat.views).label('views')
    ).filter(
        models.PostViewStat.date >= (datetime.utcnow().date() - timedelta(days=6))
    ).group_by(
        models.PostViewStat.date
    ).order_by(models.PostViewStat.date.asc()).all()

    daily_view_stats = []
    stats_map = {record.date: record.views for record in view_stats}
    for i in range(7):
        target_date = (datetime.utcnow().date() - timedelta(days=6 - i))
        daily_view_stats.append({
            "date": target_date.isoformat(),
            "views": int(stats_map.get(target_date, 0) or 0)
        })

    top_view_posts = db.query(
        models.Post.id,
        models.Post.title,
        func.sum(models.PostViewStat.views).label('views')
    ).join(
        models.PostViewStat, models.PostViewStat.post_id == models.Post.id
    ).group_by(
        models.Post.id
    ).order_by(
        func.sum(models.PostViewStat.views).desc()
    ).limit(5).all()

    return {
        "posts": {
            "total": total_posts,
            "published": published_posts,
            "draft": draft_posts,
            "encrypted": encrypted_posts,
            "pinned": pinned_posts,
            "recent": recent_posts
        },
        "categories": {
            "total": total_categories,
            "stats": category_data
        },
        "tags": {
            "total": total_tags,
            "stats": tag_data
        },
        "friends": {
            "total": total_friends,
            "enabled": enabled_friends
        },
        "latest_posts": latest_posts_data,
        "charts": {
            "daily": daily_stats,
            "monthly": monthly_stats,
            "login": login_stats_list
        },
        "analytics": {
            "total_views": total_views,
            "daily_views": daily_view_stats,
            "top_posts": [{
                "id": post.id,
                "title": post.title,
                "views": int(post.views or 0)
            } for post in top_view_posts]
        }
    }
