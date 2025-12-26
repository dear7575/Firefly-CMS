"""
搜索 API 路由
提供文章全文搜索功能
"""
from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import SessionLocal
import models
import re

router = APIRouter(prefix="/search", tags=["搜索"])


def highlight_text(text: str, keyword: str, context_length: int = 50) -> str:
    """
    在文本中高亮关键词，并返回包含关键词的上下文片段

    Args:
        text: 原始文本
        keyword: 搜索关键词
        context_length: 关键词前后显示的字符数

    Returns:
        带有 <mark> 标签的高亮文本片段
    """
    if not text or not keyword:
        return text or ""

    # 不区分大小写搜索
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    match = pattern.search(text)

    if not match:
        # 没找到匹配，返回文本开头的一部分
        return text[:context_length * 2] + "..." if len(text) > context_length * 2 else text

    start = match.start()
    end = match.end()

    # 计算上下文范围
    context_start = max(0, start - context_length)
    context_end = min(len(text), end + context_length)

    # 提取上下文
    prefix = "..." if context_start > 0 else ""
    suffix = "..." if context_end < len(text) else ""

    # 构建带高亮的文本
    before = text[context_start:start]
    matched = text[start:end]
    after = text[end:context_end]

    return f"{prefix}{before}<mark>{matched}</mark>{after}{suffix}"


def highlight_all_matches(text: str, keyword: str) -> str:
    """
    高亮文本中所有匹配的关键词

    Args:
        text: 原始文本
        keyword: 搜索关键词

    Returns:
        所有关键词都被 <mark> 标签包裹的文本
    """
    if not text or not keyword:
        return text or ""

    # 不区分大小写替换
    pattern = re.compile(f"({re.escape(keyword)})", re.IGNORECASE)
    return pattern.sub(r"<mark>\1</mark>", text)


@router.get("/", summary="搜索文章")
async def search_posts(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
):
    """
    搜索文章

    在文章标题、描述和内容中搜索关键词，返回匹配的结果。

    - **q**: 搜索关键词（必填，1-100 字符）
    - **limit**: 返回结果数量限制（默认 10，最大 50）

    返回格式兼容前端 Search.svelte 组件：
    - url: 文章 URL
    - meta.title: 带高亮的标题
    - excerpt: 带高亮的摘要/描述
    - content: 带高亮的内容片段（如果内容中匹配）
    """
    db = SessionLocal()
    try:
        keyword = q.strip()

        # 使用 LIKE 进行模糊搜索
        # 搜索标题、描述和内容
        posts = db.query(models.Post).filter(
            models.Post.is_draft == 0,  # 只搜索已发布的文章
            models.Post.password.is_(None),  # 排除加密文章
            or_(
                models.Post.title.ilike(f"%{keyword}%"),
                models.Post.description.ilike(f"%{keyword}%"),
                models.Post.content.ilike(f"%{keyword}%")
            )
        ).order_by(
            models.Post.published_at.desc()
        ).limit(limit).all()

        results = []
        for post in posts:
            # 高亮标题
            title_highlighted = highlight_all_matches(post.title, keyword)

            # 高亮描述/摘要
            description = post.description or ""
            if keyword.lower() in description.lower():
                excerpt_highlighted = highlight_text(description, keyword, 60)
            else:
                excerpt_highlighted = description[:120] + "..." if len(description) > 120 else description

            # 高亮内容片段（如果内容中有匹配）
            content_highlighted = None
            if post.content and keyword.lower() in post.content.lower():
                content_highlighted = highlight_text(post.content, keyword, 80)

            results.append({
                "url": f"/posts/{post.slug}",
                "meta": {
                    "title": title_highlighted
                },
                "excerpt": excerpt_highlighted,
                "content": content_highlighted
            })

        return results

    finally:
        db.close()
