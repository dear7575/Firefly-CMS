"""
友情链接路由模块
提供友情链接的增删改查 API 接口
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import get_db
from routes.posts import get_current_user

router = APIRouter(prefix="/friends", tags=["友情链接"])


# ============== 数据模型 ==============

class FriendLinkCreate(BaseModel):
    """创建友链请求模型"""
    title: str = Field(..., min_length=1, max_length=100, description="网站名称")
    url: str = Field(..., max_length=500, description="网站URL")
    avatar: Optional[str] = Field(None, max_length=500, description="网站头像URL")
    description: Optional[str] = Field(None, description="网站描述")
    tags: Optional[str] = Field(None, max_length=200, description="标签(逗号分隔)")
    weight: int = Field(default=0, description="排序权重")
    enabled: bool = Field(default=True, description="是否启用")


class FriendLinkUpdate(BaseModel):
    """更新友链请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="网站名称")
    url: Optional[str] = Field(None, max_length=500, description="网站URL")
    avatar: Optional[str] = Field(None, max_length=500, description="网站头像URL")
    description: Optional[str] = Field(None, description="网站描述")
    tags: Optional[str] = Field(None, max_length=200, description="标签(逗号分隔)")
    weight: Optional[int] = Field(None, description="排序权重")
    enabled: Optional[bool] = Field(None, description="是否启用")


class FriendLinkResponse(BaseModel):
    """友链响应模型"""
    id: str
    title: str
    url: str
    avatar: Optional[str]
    description: Optional[str]
    tags: Optional[str]
    weight: int
    enabled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== API 接口 ==============

@router.get("/", response_model=List[FriendLinkResponse], summary="获取友链列表")
def get_friend_links(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """获取所有友情链接列表"""
    query = db.query(models.FriendLink)
    if enabled_only:
        query = query.filter(models.FriendLink.enabled == True)

    friends = query.order_by(models.FriendLink.weight.desc()).all()
    return friends


@router.get("/{friend_id}", response_model=FriendLinkResponse, summary="获取单个友链")
def get_friend_link(friend_id: str, db: Session = Depends(get_db)):
    """根据ID获取友链详情"""
    friend = db.query(models.FriendLink).filter(models.FriendLink.id == friend_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="友链不存在")
    return friend


@router.post("/", status_code=status.HTTP_201_CREATED, summary="创建友链")
def create_friend_link(
    friend: FriendLinkCreate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """创建新友情链接"""
    # 检查URL是否已存在
    existing = db.query(models.FriendLink).filter(
        models.FriendLink.url == friend.url
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该链接已存在")

    db_friend = models.FriendLink(
        title=friend.title,
        url=friend.url,
        avatar=friend.avatar,
        description=friend.description,
        tags=friend.tags,
        weight=friend.weight,
        enabled=friend.enabled
    )

    db.add(db_friend)
    db.commit()
    db.refresh(db_friend)

    return {"message": "友链创建成功", "id": db_friend.id}


@router.put("/{friend_id}", summary="更新友链")
def update_friend_link(
    friend_id: str,
    friend: FriendLinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """更新友情链接信息"""
    db_friend = db.query(models.FriendLink).filter(
        models.FriendLink.id == friend_id
    ).first()
    if not db_friend:
        raise HTTPException(status_code=404, detail="友链不存在")

    # 检查URL是否与其他友链冲突
    if friend.url and friend.url != db_friend.url:
        existing = db.query(models.FriendLink).filter(
            models.FriendLink.url == friend.url,
            models.FriendLink.id != friend_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该链接已存在")

    # 更新字段
    update_data = friend.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_friend, key, value)

    db.commit()
    return {"message": "友链更新成功"}


@router.delete("/{friend_id}", summary="删除友链")
def delete_friend_link(
    friend_id: str,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """删除友情链接"""
    db_friend = db.query(models.FriendLink).filter(
        models.FriendLink.id == friend_id
    ).first()
    if not db_friend:
        raise HTTPException(status_code=404, detail="友链不存在")

    db.delete(db_friend)
    db.commit()
    return {"message": "友链删除成功"}
