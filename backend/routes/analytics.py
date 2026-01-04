"""
访问统计路由
"""
import hashlib
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

import models
from database import get_db

router = APIRouter(prefix="/analytics", tags=["访问统计"])


class ViewEvent(BaseModel):
    """文章访问事件"""
    post_id: Optional[str] = Field(default=None, description="文章ID")
    slug: Optional[str] = Field(default=None, description="文章别名")
    client_id: Optional[str] = Field(default=None, description="客户端唯一ID")
    referrer: Optional[str] = Field(default=None, description="来源")


@router.post("/view", summary="记录文章访问")
def record_post_view(
    event: ViewEvent,
    db: Session = Depends(get_db)
):
    """记录文章访问事件"""
    if not event.post_id and not event.slug:
        raise HTTPException(status_code=400, detail="post_id 或 slug 必须提供")

    post = None
    if event.post_id:
        post = db.query(models.Post).filter(models.Post.id == event.post_id).first()
    elif event.slug:
        post = db.query(models.Post).filter(models.Post.slug == event.slug).first()

    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    today = date.today()
    stat = db.query(models.PostViewStat).filter(
        models.PostViewStat.post_id == post.id,
        models.PostViewStat.date == today
    ).first()

    if not stat:
        stat = models.PostViewStat(
            post_id=post.id,
            date=today,
            views=0,
            unique_views=0
        )
        db.add(stat)

    stat.views = (stat.views or 0) + 1
    db.commit()

    if event.client_id:
        client_hash = hashlib.sha256(event.client_id.encode("utf-8")).hexdigest()
        client_record = models.PostViewClient(
            post_id=post.id,
            date=today,
            client_hash=client_hash
        )
        db.add(client_record)
        try:
            db.commit()
            stat.unique_views = (stat.unique_views or 0) + 1
            db.commit()
        except IntegrityError:
            db.rollback()

    return {"message": "记录成功"}


@router.get("/summary", summary="访问统计概览")
def analytics_summary(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """返回访问信息概览"""
    if days < 1 or days > 30:
        days = 7

    start_date = date.today() - timedelta(days=days - 1)

    daily_views = db.query(
        models.PostViewStat.date,
        func.sum(models.PostViewStat.views).label("views"),
        func.sum(models.PostViewStat.unique_views).label("unique_views")
    ).filter(
        models.PostViewStat.date >= start_date
    ).group_by(
        models.PostViewStat.date
    ).order_by(models.PostViewStat.date.asc()).all()

    top_posts = db.query(
        models.Post.id,
        models.Post.title,
        func.sum(models.PostViewStat.views).label("views")
    ).join(models.PostViewStat, models.PostViewStat.post_id == models.Post.id).group_by(
        models.Post.id
    ).order_by(
        func.sum(models.PostViewStat.views).desc()
    ).limit(5).all()

    total_views = db.query(func.coalesce(func.sum(models.PostViewStat.views), 0)).scalar() or 0

    return {
        "total_views": total_views,
        "daily_views": [{
            "date": record.date.isoformat(),
            "views": int(record.views or 0),
            "unique_views": int(record.unique_views or 0)
        } for record in daily_views],
        "top_posts": [{
            "id": record.id,
            "title": record.title,
            "views": int(record.views or 0)
        } for record in top_posts]
    }
