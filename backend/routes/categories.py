"""
分类路由模块
提供分类的增删改查 API 接口
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

router = APIRouter(prefix="/categories", tags=["分类管理"])


# ============== 数据模型 ==============

class CategoryCreate(BaseModel):
    """创建分类请求模型"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    slug: Optional[str] = Field(None, max_length=50, description="分类URL别名")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, max_length=100, description="分类图标")
    color: Optional[str] = Field(None, max_length=20, description="分类颜色")
    sort_order: int = Field(default=0, description="排序权重")
    enabled: bool = Field(default=True, description="是否启用")


class CategoryUpdate(BaseModel):
    """更新分类请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="分类名称")
    slug: Optional[str] = Field(None, max_length=50, description="分类URL别名")
    description: Optional[str] = Field(None, description="分类描述")
    icon: Optional[str] = Field(None, max_length=100, description="分类图标")
    color: Optional[str] = Field(None, max_length=20, description="分类颜色")
    sort_order: Optional[int] = Field(None, description="排序权重")
    enabled: Optional[bool] = Field(None, description="是否启用")


class CategoryResponse(BaseModel):
    """分类响应模型"""
    id: str
    name: str
    slug: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    sort_order: int
    enabled: bool
    post_count: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== API 接口 ==============

@router.get("", response_model=List[CategoryResponse], summary="获取分类列表")
def get_categories(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取所有分类列表"""
    query = db.query(models.Category)
    if enabled_only:
        query = query.filter(models.Category.enabled == True)

    categories = query.order_by(models.Category.sort_order.desc()).all()

    result = []
    for cat in categories:
        post_count = db.query(func.count(models.Post.id)).filter(
            models.Post.category_id == cat.id
        ).scalar()

        result.append({
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "icon": cat.icon,
            "color": cat.color,
            "sort_order": cat.sort_order,
            "enabled": cat.enabled,
            "post_count": post_count,
            "created_at": cat.created_at
        })

    return result


@router.get("/{category_id}", response_model=CategoryResponse, summary="获取单个分类")
def get_category(category_id: str, db: Session = Depends(get_db)):
    """根据ID获取分类详情"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    post_count = db.query(func.count(models.Post.id)).filter(
        models.Post.category_id == category.id
    ).scalar()

    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "icon": category.icon,
        "color": category.color,
        "sort_order": category.sort_order,
        "enabled": category.enabled,
        "post_count": post_count,
        "created_at": category.created_at
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="创建分类")
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """创建新分类"""
    # 检查名称是否已存在
    existing = db.query(models.Category).filter(
        models.Category.name == category.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类名称已存在")

    # 检查slug是否已存在
    if category.slug:
        existing_slug = db.query(models.Category).filter(
            models.Category.slug == category.slug
        ).first()
        if existing_slug:
            raise HTTPException(status_code=400, detail="分类别名已存在")

    db_category = models.Category(
        name=category.name,
        slug=category.slug or category.name.lower().replace(" ", "-"),
        description=category.description,
        icon=category.icon,
        color=category.color,
        sort_order=category.sort_order,
        enabled=category.enabled
    )

    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return {"message": "分类创建成功", "id": db_category.id}


@router.put("/{category_id}", summary="更新分类")
def update_category(
    category_id: str,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """更新分类信息"""
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查名称是否与其他分类冲突
    if category.name and category.name != db_category.name:
        existing = db.query(models.Category).filter(
            models.Category.name == category.name,
            models.Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="分类名称已存在")

    # 检查slug是否与其他分类冲突
    if category.slug and category.slug != db_category.slug:
        existing_slug = db.query(models.Category).filter(
            models.Category.slug == category.slug,
            models.Category.id != category_id
        ).first()
        if existing_slug:
            raise HTTPException(status_code=400, detail="分类别名已存在")

    # 更新字段
    update_data = category.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    return {"message": "分类更新成功"}


@router.delete("/{category_id}", summary="删除分类")
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """删除分类"""
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查是否有文章使用此分类
    post_count = db.query(func.count(models.Post.id)).filter(
        models.Post.category_id == category_id
    ).scalar()
    if post_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除：该分类下有 {post_count} 篇文章"
        )

    db.delete(db_category)
    db.commit()
    return {"message": "分类删除成功"}
