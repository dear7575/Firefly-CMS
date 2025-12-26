"""
访问日志路由模块
提供访问日志的查询和管理 API 接口
"""
from datetime import datetime, timedelta
from typing import List, Optional

import models
from database import get_db, settings
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

# 创建路由器
router = APIRouter(prefix="/logs", tags=["访问日志"])


# ============== 认证依赖 ==============

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """验证 JWT Token 并获取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌已过期或无效"
        )

    user = db.query(models.Admin).filter(models.Admin.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


# ============== 响应模型 ==============

class LogResponse(BaseModel):
    """日志响应模型"""
    id: str
    log_type: str
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_path: Optional[str]
    request_method: Optional[str]
    status_code: Optional[int]
    detail: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LogStatsResponse(BaseModel):
    """日志统计响应模型"""
    total_logs: int
    login_success_count: int
    login_failed_count: int
    api_access_count: int
    unique_ips: int
    today_logs: int


# ============== API 端点 ==============

@router.get("/", response_model=List[LogResponse], summary="获取日志列表")
async def get_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    log_type: Optional[str] = Query(None, description="日志类型筛选"),
    username: Optional[str] = Query(None, description="用户名筛选"),
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    获取访问日志列表（分页）

    - 自动清理 30 天前的日志
    - 支持按日志类型和用户名筛选
    """
    # 自动清理 30 天前的日志
    cleanup_date = datetime.utcnow() - timedelta(days=30)
    db.query(models.AccessLog).filter(
        models.AccessLog.created_at < cleanup_date
    ).delete(synchronize_session=False)
    db.commit()

    # 构建查询
    query = db.query(models.AccessLog)

    # 筛选条件
    if log_type:
        query = query.filter(models.AccessLog.log_type == log_type)
    if username:
        query = query.filter(models.AccessLog.username.like(f"%{username}%"))

    # 按时间倒序排列
    query = query.order_by(desc(models.AccessLog.created_at))

    # 分页
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    # 添加分页信息到第一条记录
    if logs:
        logs[0]._pagination = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    return logs


@router.get("/stats", response_model=LogStatsResponse, summary="获取日志统计")
async def get_log_stats(
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """获取日志统计信息"""
    # 总日志数
    total_logs = db.query(models.AccessLog).count()

    # 登录成功次数
    login_success_count = db.query(models.AccessLog).filter(
        models.AccessLog.log_type == "login_success"
    ).count()

    # 登录失败次数
    login_failed_count = db.query(models.AccessLog).filter(
        models.AccessLog.log_type == "login_failed"
    ).count()

    # API 访问次数
    api_access_count = db.query(models.AccessLog).filter(
        models.AccessLog.log_type == "api_access"
    ).count()

    # 独立 IP 数
    unique_ips = db.query(models.AccessLog.ip_address).distinct().count()

    # 今日日志数
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = db.query(models.AccessLog).filter(
        models.AccessLog.created_at >= today_start
    ).count()

    return LogStatsResponse(
        total_logs=total_logs,
        login_success_count=login_success_count,
        login_failed_count=login_failed_count,
        api_access_count=api_access_count,
        unique_ips=unique_ips,
        today_logs=today_logs
    )


@router.delete("/cleanup", summary="手动清理旧日志")
async def cleanup_logs(
    days: int = Query(30, ge=1, le=365, description="清理多少天前的日志"),
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """手动清理指定天数前的日志"""
    cleanup_date = datetime.utcnow() - timedelta(days=days)
    deleted_count = db.query(models.AccessLog).filter(
        models.AccessLog.created_at < cleanup_date
    ).delete(synchronize_session=False)
    db.commit()

    return {"message": f"已清理 {deleted_count} 条日志", "deleted_count": deleted_count}


@router.delete("/clear-all", summary="清空所有日志")
async def clear_all_logs(
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """清空所有日志记录"""
    deleted_count = db.query(models.AccessLog).delete(synchronize_session=False)
    db.commit()

    return {"message": f"已清空 {deleted_count} 条日志", "deleted_count": deleted_count}
