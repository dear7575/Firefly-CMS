"""
认证相关路由
包括登录、修改密码等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from jose import JWTError, jwt

import auth
import models
from database import get_db, settings as db_settings

router = APIRouter(prefix="/auth", tags=["认证"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class PasswordChangeRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="当前密码", min_length=1)
    new_password: str = Field(..., description="新密码", min_length=6, max_length=100)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    从 JWT Token 获取当前用户
    
    Args:
        token: JWT 访问令牌
        db: 数据库会话
        
    Returns:
        Admin: 当前登录的管理员用户
        
    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码 JWT Token
        payload = jwt.decode(
            token,
            db_settings.SECRET_KEY,
            algorithms=[db_settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 从数据库查询用户
    user = db.query(models.Admin).filter(models.Admin.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: models.Admin = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户的密码
    
    - **old_password**: 当前密码（用于验证）
    - **new_password**: 新密码（至少6个字符）
    
    返回修改结果
    """
    # 验证当前密码是否正确
    if not auth.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 检查新密码是否与旧密码相同
    if auth.verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与当前密码相同"
        )
    
    # 更新密码
    current_user.hashed_password = auth.get_password_hash(password_data.new_password)
    db.commit()
    
    return {
        "message": "密码修改成功，请使用新密码重新登录"
    }


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(current_user: models.Admin = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    
    返回用户名等基本信息
    """
    return {
        "id": current_user.id,
        "username": current_user.username
    }
