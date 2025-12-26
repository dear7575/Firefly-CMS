"""
标签路由模块
提供标签的增删改查 API 接口
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from database import get_db
from routes.posts import get_current_user

router = APIRouter(prefix="/tags", tags=["标签管理"])


# ============== 数据模型 ==============

class TagCreate(BaseModel):
    """创建标签请求模型"""
    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    slug: Optional[str] = Field(None, max_length=50, description="标签URL别名")
    color: Optional[str] = Field(None, max_length=20, description="标签颜色")
    enabled: bool = Field(default=True, description="是否启用")


class TagUpdate(BaseModel):
    """更新标签请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="标签名称")
    slug: Optional[str] = Field(None, max_length=50, description="标签URL别名")
    color: Optional[str] = Field(None, max_length=20, description="标签颜色")
    enabled: Optional[bool] = Field(None, description="是否启用")


class TagResponse(BaseModel):
    """标签响应模型"""
    id: str
    name: str
    slug: Optional[str]
    color: Optional[str]
    enabled: bool
    post_count: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== API 接口 ==============

@router.get("/", response_model=List[TagResponse], summary="获取标签列表")
def get_tags(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取所有标签列表"""
    query = db.query(models.Tag)
    if enabled_only:
        query = query.filter(models.Tag.enabled == True)

    tags = query.order_by(models.Tag.name).all()

    result = []
    for tag in tags:
        post_count = db.query(func.count(models.post_tags.c.post_id)).filter(
            models.post_tags.c.tag_id == tag.id
        ).scalar()

        result.append({
            "id": tag.id,
            "name": tag.name,
            "slug": tag.slug,
            "color": tag.color,
            "enabled": tag.enabled,
            "post_count": post_count,
            "created_at": tag.created_at
        })

    return result


@router.get("/{tag_id}", response_model=TagResponse, summary="获取单个标签")
def get_tag(tag_id: str, db: Session = Depends(get_db)):
    """根据ID获取标签详情"""
    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    post_count = db.query(func.count(models.post_tags.c.post_id)).filter(
        models.post_tags.c.tag_id == tag.id
    ).scalar()

    return {
        "id": tag.id,
        "name": tag.name,
        "slug": tag.slug,
        "color": tag.color,
        "enabled": tag.enabled,
        "post_count": post_count,
        "created_at": tag.created_at
    }


@router.post("/", status_code=status.HTTP_201_CREATED, summary="创建标签")
def create_tag(
    tag: TagCreate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """创建新标签"""
    # 检查名称是否已存在
    existing = db.query(models.Tag).filter(models.Tag.name == tag.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签名称已存在")

    # 检查slug是否已存在
    if tag.slug:
        existing_slug = db.query(models.Tag).filter(models.Tag.slug == tag.slug).first()
        if existing_slug:
            raise HTTPException(status_code=400, detail="标签别名已存在")

    db_tag = models.Tag(
        name=tag.name,
        slug=tag.slug or tag.name.lower().replace(" ", "-"),
        color=tag.color,
        enabled=tag.enabled
    )

    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)

    return {"message": "标签创建成功", "id": db_tag.id}


@router.put("/{tag_id}", summary="更新标签")
def update_tag(
    tag_id: str,
    tag: TagUpdate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """更新标签信息"""
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 检查名称是否与其他标签冲突
    if tag.name and tag.name != db_tag.name:
        existing = db.query(models.Tag).filter(
            models.Tag.name == tag.name,
            models.Tag.id != tag_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="标签名称已存在")

    # 检查slug是否与其他标签冲突
    if tag.slug and tag.slug != db_tag.slug:
        existing_slug = db.query(models.Tag).filter(
            models.Tag.slug == tag.slug,
            models.Tag.id != tag_id
        ).first()
        if existing_slug:
            raise HTTPException(status_code=400, detail="标签别名已存在")

    # 更新字段
    update_data = tag.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tag, key, value)

    db.commit()
    return {"message": "标签更新成功"}


@router.delete("/{tag_id}", summary="删除标签")
def delete_tag(
    tag_id: str,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """删除标签"""
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 检查是否有文章使用此标签
    post_count = db.query(func.count(models.post_tags.c.post_id)).filter(
        models.post_tags.c.tag_id == tag_id
    ).scalar()
    if post_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：该标签被 {post_count} 篇文章使用"
        )

    db.delete(db_tag)
    db.commit()
    return {"message": "标签删除成功"}
