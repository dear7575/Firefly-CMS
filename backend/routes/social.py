"""
社交链接路由模块
提供社交链接的增删改查 API 接口
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import get_db
from routes.posts import get_current_user

router = APIRouter(prefix="/social-links", tags=["社交链接"])


# ============== 数据模型 ==============

class SocialLinkCreate(BaseModel):
    """创建社交链接请求模型"""
    name: str = Field(..., min_length=1, max_length=50, description="平台名称")
    icon: str = Field(..., max_length=100, description="图标(iconify格式)")
    url: str = Field(..., max_length=500, description="链接URL")
    show_name: bool = Field(default=False, description="是否显示名称")
    sort_order: int = Field(default=0, description="排序权重")
    enabled: bool = Field(default=True, description="是否启用")


class SocialLinkUpdate(BaseModel):
    """更新社交链接请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="平台名称")
    icon: Optional[str] = Field(None, max_length=100, description="图标(iconify格式)")
    url: Optional[str] = Field(None, max_length=500, description="链接URL")
    show_name: Optional[bool] = Field(None, description="是否显示名称")
    sort_order: Optional[int] = Field(None, description="排序权重")
    enabled: Optional[bool] = Field(None, description="是否启用")


class SocialLinkResponse(BaseModel):
    """社交链接响应模型"""
    id: str
    name: str
    icon: str
    url: str
    show_name: bool
    sort_order: int
    enabled: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== API 接口 ==============

@router.get("/", response_model=List[SocialLinkResponse], summary="获取社交链接列表")
def get_social_links(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取所有社交链接列表"""
    query = db.query(models.SocialLink)
    if enabled_only:
        query = query.filter(models.SocialLink.enabled == True)

    links = query.order_by(models.SocialLink.sort_order.desc()).all()
    return links


@router.get("/{link_id}", response_model=SocialLinkResponse, summary="获取单个社交链接")
def get_social_link(link_id: str, db: Session = Depends(get_db)):
    """根据ID获取社交链接详情"""
    link = db.query(models.SocialLink).filter(models.SocialLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="社交链接不存在")
    return link


@router.post("/", status_code=status.HTTP_201_CREATED, summary="创建社交链接")
def create_social_link(
    link: SocialLinkCreate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """创建新社交链接"""
    db_link = models.SocialLink(
        name=link.name,
        icon=link.icon,
        url=link.url,
        show_name=link.show_name,
        sort_order=link.sort_order,
        enabled=link.enabled
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    return {"message": "社交链接创建成功", "id": db_link.id}


@router.put("/{link_id}", summary="更新社交链接")
def update_social_link(
    link_id: str,
    link: SocialLinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """更新社交链接信息"""
    db_link = db.query(models.SocialLink).filter(
        models.SocialLink.id == link_id
    ).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="社交链接不存在")

    # 更新字段
    update_data = link.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_link, key, value)

    db.commit()
    return {"message": "社交链接更新成功"}


@router.delete("/{link_id}", summary="删除社交链接")
def delete_social_link(
    link_id: str,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """删除社交链接"""
    db_link = db.query(models.SocialLink).filter(
        models.SocialLink.id == link_id
    ).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="社交链接不存在")

    db.delete(db_link)
    db.commit()
    return {"message": "社交链接删除成功"}
