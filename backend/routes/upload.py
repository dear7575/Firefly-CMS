"""
文件上传路由
提供图片和文件上传功能
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime
import os
import uuid
import shutil
from typing import Optional, List

from database import get_db, settings
import models

router = APIRouter(prefix="/upload", tags=["文件上传"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}

# 允许的文件类型（包括图片）
ALLOWED_FILE_TYPES = {
    **ALLOWED_IMAGE_TYPES,
    "application/pdf": ".pdf",
    "application/zip": ".zip",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


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


def generate_unique_filename(original_filename: str, extension: str) -> str:
    """生成唯一文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}{extension}"


def get_upload_path(subdir: str = "") -> str:
    """获取上传目录路径"""
    base_path = settings.UPLOAD_DIR
    if subdir:
        path = os.path.join(base_path, subdir)
    else:
        path = base_path
    os.makedirs(path, exist_ok=True)
    return path


@router.post("/image", summary="上传图片")
async def upload_image(
    file: UploadFile = File(...),
    subdir: Optional[str] = Form(default="images"),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    上传单张图片

    - **file**: 图片文件
    - **subdir**: 子目录（默认 images）

    返回图片访问 URL
    """
    # 验证文件类型
    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片类型: {content_type}。支持的类型: {', '.join(ALLOWED_IMAGE_TYPES.keys())}"
        )

    # 验证文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()  # 获取文件大小
    file.file.seek(0)  # 重置到文件开头

    max_size = settings.MAX_UPLOAD_SIZE * 1024 * 1024  # 转换为字节
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制。最大允许: {settings.MAX_UPLOAD_SIZE}MB"
        )

    # 生成唯一文件名
    extension = ALLOWED_IMAGE_TYPES[content_type]
    filename = generate_unique_filename(file.filename or "image", extension)

    # 保存文件
    upload_path = get_upload_path(subdir)
    file_path = os.path.join(upload_path, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 返回访问 URL
    url = f"/uploads/{subdir}/{filename}" if subdir else f"/uploads/{filename}"
    return {
        "url": url,
        "filename": filename,
        "size": file_size,
        "content_type": content_type
    }


@router.post("/images", summary="批量上传图片")
async def upload_images(
    files: List[UploadFile] = File(...),
    subdir: Optional[str] = Form(default="images"),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    批量上传图片

    - **files**: 图片文件列表
    - **subdir**: 子目录（默认 images）

    返回图片访问 URL 列表
    """
    results = []
    errors = []

    for file in files:
        try:
            # 验证文件类型
            content_type = file.content_type
            if content_type not in ALLOWED_IMAGE_TYPES:
                errors.append({
                    "filename": file.filename,
                    "error": f"不支持的图片类型: {content_type}"
                })
                continue

            # 验证文件大小
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

            max_size = settings.MAX_UPLOAD_SIZE * 1024 * 1024
            if file_size > max_size:
                errors.append({
                    "filename": file.filename,
                    "error": f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE}MB)"
                })
                continue

            # 生成唯一文件名并保存
            extension = ALLOWED_IMAGE_TYPES[content_type]
            filename = generate_unique_filename(file.filename or "image", extension)
            upload_path = get_upload_path(subdir)
            file_path = os.path.join(upload_path, filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            url = f"/uploads/{subdir}/{filename}" if subdir else f"/uploads/{filename}"
            results.append({
                "url": url,
                "filename": filename,
                "original_name": file.filename,
                "size": file_size
            })

        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "success": results,
        "errors": errors,
        "total": len(files),
        "uploaded": len(results),
        "failed": len(errors)
    }


@router.delete("/{subdir}/{filename}", summary="删除文件")
async def delete_file(
    subdir: str,
    filename: str,
    current_user: models.Admin = Depends(get_current_user)
):
    """
    删除已上传的文件

    - **subdir**: 子目录
    - **filename**: 文件名
    """
    file_path = os.path.join(settings.UPLOAD_DIR, subdir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 安全检查：确保路径在上传目录内
    real_path = os.path.realpath(file_path)
    upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not real_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="禁止访问")

    try:
        os.remove(file_path)
        return {"message": "文件删除成功", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/list/{subdir}", summary="列出目录文件")
async def list_files(
    subdir: str,
    current_user: models.Admin = Depends(get_current_user)
):
    """
    列出指定目录下的所有文件

    - **subdir**: 子目录
    """
    dir_path = os.path.join(settings.UPLOAD_DIR, subdir)

    if not os.path.exists(dir_path):
        return {"files": [], "total": 0}

    # 安全检查
    real_path = os.path.realpath(dir_path)
    upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not real_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="禁止访问")

    files = []
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files.append({
                "filename": filename,
                "url": f"/uploads/{subdir}/{filename}",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    # 按修改时间倒序排列
    files.sort(key=lambda x: x["modified"], reverse=True)

    return {"files": files, "total": len(files)}
