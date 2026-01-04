"""
文件上传路由
提供图片和文件上传功能
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime
import os
import uuid
import shutil
from typing import Optional, List

from sqlalchemy import func, or_

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


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """验证 JWT Token 并获取当前用户"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.split(" ")[1]

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


def build_media_url(filename: str, subdir: Optional[str]) -> str:
    """构建可访问的 URL"""
    clean_subdir = (subdir or "").strip().replace("\\", "/").strip("/")
    if clean_subdir:
        return f"/uploads/{clean_subdir}/{filename}"
    return f"/uploads/{filename}"


def build_media_path(filename: str, subdir: Optional[str]) -> str:
    """构建相对路径"""
    clean_subdir = (subdir or "").strip().replace("\\", "/").strip("/")
    if clean_subdir:
        return f"{clean_subdir}/{filename}"
    return filename


def record_media_file(
    db: Session,
    filename: str,
    original_name: Optional[str],
    content_type: Optional[str],
    size: int,
    subdir: Optional[str],
    uploader: Optional[str]
) -> models.MediaFile:
    """将上传文件写入媒体库"""
    media = models.MediaFile(
        filename=filename,
        original_name=original_name,
        mime_type=content_type,
        size=size,
        url=build_media_url(filename, subdir),
        path=build_media_path(filename, subdir),
        uploader=uploader
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@router.post("/image", summary="上传图片")
async def upload_image(
    file: UploadFile = File(...),
    subdir: Optional[str] = Form(default="images"),
    db: Session = Depends(get_db),
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
    media = record_media_file(
        db=db,
        filename=filename,
        original_name=file.filename,
        content_type=content_type,
        size=file_size,
        subdir=subdir,
        uploader=current_user.username if current_user else None
    )
    return {
        "url": url,
        "filename": filename,
        "size": file_size,
        "content_type": content_type,
        "media_id": media.id
    }


@router.post("/images", summary="批量上传文件")
async def upload_images(
    files: List[UploadFile] = File(...),
    subdir: Optional[str] = Form(default="images"),
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    批量上传文件

    - **files**: 文件列表
    - **subdir**: 子目录（默认 images）

    返回文件访问 URL 列表
    """
    results = []
    errors = []

    for file in files:
        try:
            # 验证文件类型
            content_type = file.content_type
            if content_type not in ALLOWED_FILE_TYPES:
                errors.append({
                    "filename": file.filename,
                    "error": f"不支持的文件类型: {content_type}"
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
            extension = ALLOWED_FILE_TYPES[content_type]
            filename = generate_unique_filename(file.filename or "file", extension)
            upload_path = get_upload_path(subdir)
            file_path = os.path.join(upload_path, filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            url = f"/uploads/{subdir}/{filename}" if subdir else f"/uploads/{filename}"
            media = record_media_file(
                db=db,
                filename=filename,
                original_name=file.filename,
                content_type=content_type,
                size=file_size,
                subdir=subdir,
                uploader=current_user.username if current_user else None
            )
            results.append({
                "url": url,
                "filename": filename,
                "original_name": file.filename,
                "size": file_size,
                "media_id": media.id
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


@router.delete("/folder/{path:path}", summary="删除文件夹")
async def delete_folder(
    path: str,
    current_user: models.Admin = Depends(get_current_user)
):
    """
    删除文件夹（必须为空）

    - **path**: 文件夹路径
    """
    folder_path = os.path.join(settings.UPLOAD_DIR, path)

    # 安全检查
    real_path = os.path.realpath(folder_path)
    upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not real_path.startswith(upload_dir) or real_path == upload_dir:
        raise HTTPException(status_code=403, detail="禁止访问")

    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="不是文件夹")

    # 检查是否为空
    if os.listdir(folder_path):
        raise HTTPException(status_code=400, detail="文件夹不为空，请先删除内部文件")

    try:
        os.rmdir(folder_path)
        return {"message": "文件夹删除成功", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.put("/folder/{path:path}", summary="重命名文件夹")
async def rename_folder(
    path: str,
    new_name: str = Form(...),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    重命名文件夹

    - **path**: 原文件夹路径
    - **new_name**: 新文件夹名称
    """
    # 验证新名称
    if not new_name or ".." in new_name or "/" in new_name or "\\" in new_name:
        raise HTTPException(status_code=400, detail="无效的文件夹名称")

    folder_path = os.path.join(settings.UPLOAD_DIR, path)

    # 安全检查
    real_path = os.path.realpath(folder_path)
    upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not real_path.startswith(upload_dir) or real_path == upload_dir:
        raise HTTPException(status_code=403, detail="禁止访问")

    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="不是文件夹")

    # 构建新路径
    parent_dir = os.path.dirname(folder_path)
    new_path = os.path.join(parent_dir, new_name)

    # 检查新路径是否已存在
    if os.path.exists(new_path):
        raise HTTPException(status_code=400, detail="目标文件夹已存在")

    try:
        shutil.move(folder_path, new_path)
        # 计算相对路径
        new_relative_path = os.path.relpath(new_path, settings.UPLOAD_DIR).replace("\\", "/")
        return {"message": "文件夹重命名成功", "old_path": path, "new_path": new_relative_path}
    except PermissionError:
        raise HTTPException(status_code=500, detail="文件夹被占用，请关闭相关程序后重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重命名失败: {str(e)}")


@router.delete("/{subdir}/{filename}", summary="删除文件")
async def delete_file(
    subdir: str,
    filename: str,
    db: Session = Depends(get_db),
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
        db.query(models.MediaFile).filter(
            models.MediaFile.path == build_media_path(filename, subdir)
        ).delete(synchronize_session=False)
        db.commit()
        return {"message": "文件删除成功", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/media", summary="获取媒体文件列表")
async def get_media_files(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """分页列出媒体文件"""
    query = db.query(models.MediaFile)
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                models.MediaFile.filename.ilike(like_pattern),
                models.MediaFile.original_name.ilike(like_pattern),
                models.MediaFile.uploader.ilike(like_pattern)
            )
        )

    total = query.count()
    files = query.order_by(models.MediaFile.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [{
            "id": media.id,
            "filename": media.filename,
            "original_name": media.original_name,
            "mime_type": media.mime_type,
            "size": media.size,
            "url": media.url,
            "path": media.path,
            "uploader": media.uploader,
            "width": media.width,
            "height": media.height,
            "usage_count": media.usage_count,
            "created_at": media.created_at
        } for media in files],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/media/stats", summary="获取媒体统计信息")
async def get_media_stats(
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """获取媒体库统计数据"""
    total_files = db.query(func.count(models.MediaFile.id)).scalar() or 0
    total_size = db.query(func.coalesce(func.sum(models.MediaFile.size), 0)).scalar() or 0
    latest = db.query(models.MediaFile).order_by(models.MediaFile.created_at.desc()).first()

    return {
        "total_files": total_files,
        "total_size": total_size,
        "last_upload": {
            "filename": latest.filename,
            "created_at": latest.created_at
        } if latest else None
    }


@router.delete("/media/{media_id}", summary="删除媒体记录")
async def delete_media_record(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(get_current_user)
):
    """删除媒体文件记录并移除磁盘文件"""
    media = db.query(models.MediaFile).filter(models.MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="媒体文件不存在")

    file_path = os.path.join(settings.UPLOAD_DIR, media.path.replace("/", os.sep))
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"删除文件失败: {exc}")

    db.delete(media)
    db.commit()
    return {"message": "媒体文件已删除"}


@router.get("/list", summary="列出根目录")
async def list_root(
    current_user: models.Admin = Depends(get_current_user)
):
    """列出上传根目录下的所有文件和文件夹"""
    dir_path = settings.UPLOAD_DIR

    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        return {"files": [], "folders": [], "total": 0, "current_path": ""}

    files = []
    folders = []

    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        stat = os.stat(file_path)

        if os.path.isdir(file_path):
            try:
                item_count = len([f for f in os.listdir(file_path)])
            except:
                item_count = 0

            folders.append({
                "name": filename,
                "path": filename,
                "item_count": item_count,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        else:
            files.append({
                "filename": filename,
                "url": f"/uploads/{filename}",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    folders.sort(key=lambda x: x["name"])
    files.sort(key=lambda x: x["modified"], reverse=True)

    return {
        "files": files,
        "folders": folders,
        "total": len(files) + len(folders),
        "current_path": ""
    }


@router.get("/list/{subdir:path}", summary="列出目录文件")
async def list_files(
    subdir: str,
    current_user: models.Admin = Depends(get_current_user)
):
    """
    列出指定目录下的所有文件和文件夹

    - **subdir**: 子目录路径（支持多级，如 images/2024）
    """
    # 处理空路径
    if not subdir or subdir == "/":
        dir_path = settings.UPLOAD_DIR
        subdir = ""
    else:
        dir_path = os.path.join(settings.UPLOAD_DIR, subdir)

    if not os.path.exists(dir_path):
        return {"files": [], "folders": [], "total": 0, "current_path": subdir}

    # 安全检查
    real_path = os.path.realpath(dir_path)
    upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not real_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="禁止访问")

    files = []
    folders = []

    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        stat = os.stat(file_path)

        if os.path.isdir(file_path):
            # 统计文件夹内的文件数量
            try:
                item_count = len([f for f in os.listdir(file_path)])
            except:
                item_count = 0

            folders.append({
                "name": filename,
                "path": f"{subdir}/{filename}" if subdir else filename,
                "item_count": item_count,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        else:
            url_path = f"{subdir}/{filename}" if subdir else filename
            files.append({
                "filename": filename,
                "url": f"/uploads/{url_path}",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    # 文件夹按名称排序，文件按修改时间倒序
    folders.sort(key=lambda x: x["name"])
    files.sort(key=lambda x: x["modified"], reverse=True)

    return {
        "files": files,
        "folders": folders,
        "total": len(files) + len(folders),
        "current_path": subdir
    }


@router.post("/folder", summary="创建文件夹")
async def create_folder(
    path: str = Form(...),
    current_user: models.Admin = Depends(get_current_user)
):
    """
    创建新文件夹

    - **path**: 文件夹路径（如 images/2024/photos）
    """
    # 验证路径安全性
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="无效的文件夹路径")

    folder_path = os.path.join(settings.UPLOAD_DIR, path)

    # 安全检查
    real_path = os.path.realpath(folder_path)
    upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not real_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="禁止访问")

    if os.path.exists(folder_path):
        raise HTTPException(status_code=400, detail="文件夹已存在")

    try:
        os.makedirs(folder_path, exist_ok=True)
        return {"message": "文件夹创建成功", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


def build_folder_tree(dir_path: str, base_path: str, relative_path: str = "") -> list:
    """递归构建文件夹树结构"""
    tree = []
    if not os.path.exists(dir_path):
        return tree
    try:
        items = os.listdir(dir_path)
    except PermissionError:
        return tree

    for item in sorted(items):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path):
            item_relative_path = f"{relative_path}/{item}" if relative_path else item
            try:
                item_count = len(os.listdir(item_path))
            except:
                item_count = 0
            children = build_folder_tree(item_path, base_path, item_relative_path)
            tree.append({
                "name": item,
                "path": item_relative_path,
                "item_count": item_count,
                "children": children
            })
    return tree


@router.get("/folder-tree", summary="获取完整目录树")
async def get_folder_tree(
    current_user: models.Admin = Depends(get_current_user)
):
    """获取完整的文件夹树结构，用于左侧目录树显示"""
    upload_dir = settings.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    tree = build_folder_tree(upload_dir, upload_dir, "")
    return {
        "tree": tree,
        "root": {
            "name": "根目录",
            "path": "",
            "item_count": len(os.listdir(upload_dir)) if os.path.exists(upload_dir) else 0
        }
    }


def get_directory_size(path: str) -> int:
    """递归计算目录大小"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_directory_size(entry.path)
    except PermissionError:
        pass
    return total


@router.get("/storage-info", summary="获取存储空间信息")
async def get_storage_info(
    current_user: models.Admin = Depends(get_current_user)
):
    """获取上传目录的存储空间使用情况"""
    upload_dir = settings.UPLOAD_DIR

    if not os.path.exists(upload_dir):
        return {
            "total_size": 0,
            "file_count": 0,
            "folder_count": 0
        }

    total_size = get_directory_size(upload_dir)
    file_count = 0
    folder_count = 0

    for root, dirs, files in os.walk(upload_dir):
        file_count += len(files)
        folder_count += len(dirs)

    return {
        "total_size": total_size,
        "file_count": file_count,
        "folder_count": folder_count
    }
