"""
媒体引用统计工具
用于解析文章中的上传文件引用并维护引用关系
"""
from typing import Dict, Iterable, Optional, Set
from urllib.parse import urlparse, unquote
import re

from sqlalchemy import func
from sqlalchemy.orm import Session

import models

# 匹配 /uploads/ 引用（支持绝对 URL 和相对路径）
UPLOAD_URL_PATTERN = re.compile(
    r"(?:https?:)?//[^\s\"'<>]+/uploads/[^\s\"'<>]+|/uploads/[^\s\"'<>]+",
    re.IGNORECASE
)


def normalize_upload_path(url: str) -> Optional[str]:
    """将上传资源 URL 规范化为相对路径"""
    if not url:
        return None
    cleaned = url.strip()
    # 去掉 Markdown/HTML 可能携带的收尾符号
    cleaned = cleaned.rstrip(").,;:]>\"'")
    if cleaned.startswith("//"):
        cleaned = "https:" + cleaned
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        parsed = urlparse(cleaned)
        path = parsed.path
    else:
        path = cleaned

    if "/uploads/" not in path:
        return None

    relative = path.split("/uploads/", 1)[1].lstrip("/")
    if not relative:
        return None
    return unquote(relative)


def extract_upload_paths(text: Optional[str]) -> Set[str]:
    """从文本中提取上传资源路径集合"""
    if not text:
        return set()
    paths: Set[str] = set()
    for match in UPLOAD_URL_PATTERN.findall(text):
        normalized = normalize_upload_path(match)
        if normalized:
            paths.add(normalized)
    return paths


def collect_media_paths(content: Optional[str], image: Optional[str]) -> Dict[str, str]:
    """汇总文章引用媒体并标记使用场景"""
    path_context: Dict[str, str] = {}
    for path in extract_upload_paths(content):
        path_context[path] = "content"

    cover_path = normalize_upload_path(image or "")
    if cover_path and cover_path not in path_context:
        path_context[cover_path] = "cover"
    return path_context


def refresh_media_usage_counts(db: Session, media_ids: Iterable[str]) -> None:
    """刷新指定媒体的引用次数"""
    media_id_list = [media_id for media_id in set(media_ids) if media_id]
    if not media_id_list:
        return

    counts = dict(
        db.query(models.PostMedia.media_id, func.count(models.PostMedia.id))
        .filter(models.PostMedia.media_id.in_(media_id_list))
        .group_by(models.PostMedia.media_id)
        .all()
    )

    for media_id in media_id_list:
        db.query(models.MediaFile).filter(
            models.MediaFile.id == media_id
        ).update({"usage_count": counts.get(media_id, 0)})


def sync_post_media(
    db: Session,
    post_id: str,
    content: Optional[str],
    image: Optional[str]
) -> Dict[str, int]:
    """同步单篇文章的媒体引用关系"""
    path_context = collect_media_paths(content, image)
    existing_links = db.query(models.PostMedia).filter(
        models.PostMedia.post_id == post_id
    ).all()
    existing_media_ids = {link.media_id for link in existing_links}

    if not path_context:
        if existing_media_ids:
            db.query(models.PostMedia).filter(
                models.PostMedia.post_id == post_id
            ).delete(synchronize_session=False)
            db.flush()
            refresh_media_usage_counts(db, existing_media_ids)
            db.commit()
        return {"added": 0, "removed": len(existing_media_ids)}

    media_records = db.query(models.MediaFile).filter(
        models.MediaFile.path.in_(list(path_context.keys()))
    ).all()
    media_by_id = {media.id: media for media in media_records}
    new_media_ids = set(media_by_id.keys())
    to_add = new_media_ids - existing_media_ids
    to_remove = existing_media_ids - new_media_ids

    if to_remove:
        db.query(models.PostMedia).filter(
            models.PostMedia.post_id == post_id,
            models.PostMedia.media_id.in_(list(to_remove))
        ).delete(synchronize_session=False)

    for media_id in to_add:
        media = media_by_id.get(media_id)
        if not media:
            continue
        context = path_context.get(media.path)
        db.add(models.PostMedia(
            post_id=post_id,
            media_id=media_id,
            context=context
        ))

    db.flush()
    refresh_media_usage_counts(db, to_add | to_remove)
    db.commit()
    return {"added": len(to_add), "removed": len(to_remove)}


def rebuild_media_usage(db: Session) -> Dict[str, int]:
    """重建所有文章的媒体引用关系"""
    media_records = db.query(models.MediaFile).all()
    media_by_path = {media.path: media.id for media in media_records}
    media_counts = {media.id: 0 for media in media_records}

    db.query(models.PostMedia).delete(synchronize_session=False)
    db.flush()

    posts = db.query(models.Post).all()
    relations: list = []

    for post in posts:
        path_context = collect_media_paths(post.content, post.image)
        for path, context in path_context.items():
            media_id = media_by_path.get(path)
            if not media_id:
                continue
            relations.append(models.PostMedia(
                post_id=post.id,
                media_id=media_id,
                context=context
            ))
            media_counts[media_id] = media_counts.get(media_id, 0) + 1

    if relations:
        db.bulk_save_objects(relations)

    for media in media_records:
        media.usage_count = media_counts.get(media.id, 0)

    db.commit()

    return {
        "posts": len(posts),
        "media": len(media_records),
        "links": len(relations)
    }
