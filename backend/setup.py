"""
Firefly CMS 数据库初始化脚本
整合数据库表创建、管理员账户、站点设置、演示数据等初始化功能

使用方法:
    python setup.py                  # 基础初始化（表结构 + 管理员 + 默认设置）
    python setup.py --demo           # 基础初始化 + 演示数据（分类、标签、示例文章）
    python setup.py --full           # 完整初始化（基础 + 演示数据 + 前端配置导入）
    python setup.py --import-posts   # 导入静态 Markdown 文章到数据库
    python setup.py --reset          # 重置数据库（危险：删除所有数据后重新初始化）
"""
import sys
import re
from datetime import datetime
from pathlib import Path
from database import engine, Base, SessionLocal
import models
from auth import get_password_hash

# 尝试导入 yaml（用于静态文章导入）
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# 静态文章目录
POSTS_DIR = Path(__file__).parent.parent / "src" / "content" / "posts"


# ============================================================================
# 默认站点配置项
# ============================================================================
DEFAULT_SITE_SETTINGS = [
    # 基本信息
    {"key": "site_title", "value": "Firefly", "type": "string", "group": "basic", "label": "站点标题", "description": "网站的主标题，显示在浏览器标签和导航栏", "sort_order": 100},
    {"key": "site_subtitle", "value": "A beautiful blog", "type": "string", "group": "basic", "label": "站点副标题", "description": "网站的副标题或口号", "sort_order": 99},
    {"key": "site_description", "value": "A modern blog powered by Firefly", "type": "text", "group": "basic", "label": "站点描述", "description": "用于SEO的网站描述，显示在搜索结果中", "sort_order": 98},
    {"key": "site_keywords", "value": "blog,firefly,astro", "type": "string", "group": "basic", "label": "站点关键词", "description": "用于SEO的关键词，用逗号分隔", "sort_order": 97},
    {"key": "site_url", "value": "http://localhost:4321", "type": "string", "group": "basic", "label": "站点URL", "description": "网站的完整URL地址", "sort_order": 96},
    {"key": "site_lang", "value": "zh_CN", "type": "string", "group": "basic", "label": "站点语言", "description": "网站的默认语言(en/zh_CN/zh_TW/ja/ru)", "sort_order": 95},
    {"key": "site_start_date", "value": "", "type": "string", "group": "basic", "label": "建站日期", "description": "网站创建日期，格式: YYYY-MM-DD", "sort_order": 94},

    # 品牌设置
    {"key": "brand_logo", "value": "", "type": "string", "group": "brand", "label": "网站Logo", "description": "导航栏Logo图片URL，留空使用默认", "sort_order": 100},
    {"key": "brand_logo_type", "value": "icon", "type": "string", "group": "brand", "label": "Logo类型", "description": "Logo类型: icon(图标) 或 image(图片)", "sort_order": 99},
    {"key": "brand_favicon", "value": "/assets/images/favicon.ico", "type": "string", "group": "brand", "label": "网站图标", "description": "浏览器标签页图标(favicon)", "sort_order": 98},
    {"key": "brand_navbar_title", "value": "", "type": "string", "group": "brand", "label": "导航栏标题", "description": "导航栏显示的标题，留空使用站点标题", "sort_order": 97},

    # 个人资料
    {"key": "profile_avatar", "value": "/assets/images/avatar.webp", "type": "string", "group": "profile", "label": "头像", "description": "个人头像图片URL", "sort_order": 100},
    {"key": "profile_name", "value": "Firefly", "type": "string", "group": "profile", "label": "昵称", "description": "显示在侧边栏的昵称", "sort_order": 99},
    {"key": "profile_bio", "value": "Hello, I'm Firefly.", "type": "text", "group": "profile", "label": "个人签名", "description": "个人简介或签名", "sort_order": 98},

    # 主题设置
    {"key": "theme_hue", "value": "165", "type": "number", "group": "theme", "label": "主题色相", "description": "主题颜色的色相值(0-360)", "sort_order": 100},
    {"key": "theme_fixed", "value": "false", "type": "boolean", "group": "theme", "label": "固定主题色", "description": "是否固定主题色，禁止用户切换", "sort_order": 99},
    {"key": "theme_default_mode", "value": "system", "type": "string", "group": "theme", "label": "默认主题模式", "description": "默认主题模式: light/dark/system", "sort_order": 98},

    # 页脚设置
    {"key": "footer_icp", "value": "", "type": "string", "group": "footer", "label": "ICP备案号", "description": "网站ICP备案号", "sort_order": 100},
    {"key": "footer_icp_url", "value": "https://beian.miit.gov.cn/", "type": "string", "group": "footer", "label": "备案链接", "description": "备案查询链接", "sort_order": 99},
    {"key": "footer_copyright", "value": "", "type": "string", "group": "footer", "label": "版权信息", "description": "自定义版权信息", "sort_order": 98},
    {"key": "footer_powered_by", "value": "true", "type": "boolean", "group": "footer", "label": "显示Powered by", "description": "是否显示Powered by Firefly", "sort_order": 97},
    {"key": "footer_custom_html", "value": "", "type": "text", "group": "footer", "label": "自定义HTML", "description": "页脚自定义HTML内容", "sort_order": 96},

    # 功能开关
    {"key": "feature_comment", "value": "true", "type": "boolean", "group": "feature", "label": "评论功能", "description": "是否启用评论功能", "sort_order": 100},
    {"key": "feature_search", "value": "true", "type": "boolean", "group": "feature", "label": "搜索功能", "description": "是否启用搜索功能", "sort_order": 99},
    {"key": "feature_rss", "value": "true", "type": "boolean", "group": "feature", "label": "RSS订阅", "description": "是否启用RSS订阅", "sort_order": 98},
    {"key": "feature_archive", "value": "true", "type": "boolean", "group": "feature", "label": "归档页面", "description": "是否启用归档页面", "sort_order": 97},
    {"key": "feature_friends", "value": "true", "type": "boolean", "group": "feature", "label": "友链页面", "description": "是否启用友链页面", "sort_order": 96},

    # 评论设置
    {"key": "comment_type", "value": "twikoo", "type": "string", "group": "comment", "label": "评论系统类型", "description": "可选: none/twikoo/waline/giscus/disqus/artalk", "sort_order": 100},
    {"key": "comment_twikoo_env_id", "value": "", "type": "string", "group": "comment", "label": "Twikoo EnvId", "description": "Twikoo 服务地址或环境 ID", "sort_order": 99},
    {"key": "comment_twikoo_lang", "value": "zh-CN", "type": "string", "group": "comment", "label": "Twikoo 语言", "description": "Twikoo 语言设置", "sort_order": 98},
    {"key": "comment_twikoo_visitor_count", "value": "true", "type": "boolean", "group": "comment", "label": "访问量统计", "description": "是否启用文章访问量统计", "sort_order": 97},

    # 文章设置
    {"key": "post_per_page", "value": "10", "type": "number", "group": "post", "label": "每页文章数", "description": "文章列表每页显示的文章数量", "sort_order": 100},
    {"key": "post_default_layout", "value": "list", "type": "string", "group": "post", "label": "默认布局", "description": "文章列表默认布局: list/grid", "sort_order": 99},
    {"key": "post_show_toc", "value": "true", "type": "boolean", "group": "post", "label": "显示目录", "description": "是否在文章页显示目录", "sort_order": 98},
    {"key": "post_show_updated", "value": "true", "type": "boolean", "group": "post", "label": "显示更新时间", "description": "是否显示文章更新时间", "sort_order": 97},
]


# ============================================================================
# 演示数据 - 分类
# ============================================================================
DEMO_CATEGORIES = [
    {
        "name": "文章示例",
        "slug": "article-examples",
        "description": "各种 Markdown 和功能演示文章",
        "color": "#3b82f6",
        "enabled": True,
    },
    {
        "name": "博客指南",
        "slug": "blog-guide",
        "description": "Firefly CMS 博客使用指南和教程",
        "color": "#10b981",
        "enabled": True,
    },
]


# ============================================================================
# 演示数据 - 标签
# ============================================================================
DEMO_TAGS = [
    {"name": "Firefly", "slug": "firefly", "color": "#f59e0b", "enabled": True},
    {"name": "Markdown", "slug": "markdown", "color": "#6366f1", "enabled": True},
    {"name": "博客", "slug": "blog", "color": "#ec4899", "enabled": True},
    {"name": "使用指南", "slug": "guide", "color": "#14b8a6", "enabled": True},
    {"name": "示例", "slug": "demo", "color": "#f97316", "enabled": True},
    {"name": "KaTeX", "slug": "katex", "color": "#06b6d4", "enabled": True},
    {"name": "Mermaid", "slug": "mermaid", "color": "#a855f7", "enabled": True},
    {"name": "主题", "slug": "theme", "color": "#22c55e", "enabled": True},
    {"name": "开源", "slug": "opensource", "color": "#64748b", "enabled": True},
]


# ============================================================================
# 演示数据 - 文章
# ============================================================================
DEMO_POSTS = [
    {
        "title": "欢迎使用 Firefly CMS",
        "slug": "welcome-to-firefly-cms",
        "description": "Firefly CMS 是基于 Firefly 主题的动态博客内容管理系统，在保留原有精美前端的基础上，新增了完整的后台管理系统。",
        "content": """## 🌟 欢迎使用 Firefly CMS

**Firefly CMS** 是基于 [CuteLeaf/Firefly](https://github.com/CuteLeaf/Firefly) 主题的二次开发项目，在保留原有精美前端的基础上，新增了完整的后台管理系统。

## ✨ 主要特性

### 后台管理系统
- **FastAPI 后端** - 基于 Python 的高性能异步 API 服务
- **MySQL 数据库** - 数据持久化存储，支持 UUID 主键
- **JWT 认证** - 安全的用户认证机制
- **RESTful API** - 标准化的接口设计

### 管理功能
- **文章管理** - 在线编辑器（Vditor）、草稿/发布、置顶排序、密码保护
- **分类管理** - 分类的增删改查、颜色标识、启用/禁用
- **标签管理** - 标签的增删改查、颜色标识、启用/禁用
- **友链管理** - 友情链接管理、排序权重、头像/描述
- **系统设置** - 站点信息、个人资料、主题配置等动态管理

## 🚀 开始使用

1. 访问后台管理：`/admin/`
2. 默认账号：`admin` / `admin123`
3. **请登录后立即修改密码！**

## 📖 更多信息

- [GitHub 仓库](https://github.com/dear7575/Firefly-CMS)
- [原始 Firefly 主题](https://github.com/CuteLeaf/Firefly)
""",
        "category": "博客指南",
        "tags": ["Firefly", "博客", "使用指南"],
        "published_at": datetime.now(),
        "pinned": True,
        "is_draft": 0,
    },
    {
        "title": "Markdown 基础语法示例",
        "slug": "markdown-basic-example",
        "description": "展示 Firefly 主题对 Markdown 基础语法的支持，包括标题、列表、代码块等。",
        "content": """## Markdown 基础语法

### 标题

使用 `#` 符号创建标题，支持 1-6 级标题。

### 列表

**无序列表：**
- 项目一
- 项目二
- 项目三

**有序列表：**
1. 第一步
2. 第二步
3. 第三步

### 代码块

行内代码：`console.log('Hello World')`

代码块：

```javascript
function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet('Firefly'));
```

### 引用

> 这是一段引用文字。
> 可以包含多行内容。

### 链接和图片

[访问 GitHub](https://github.com)

### 表格

| 功能 | 描述 | 状态 |
|------|------|------|
| 文章管理 | 在线编辑器 | ✅ |
| 分类管理 | 颜色标识 | ✅ |
| 标签管理 | 启用/禁用 | ✅ |
""",
        "category": "文章示例",
        "tags": ["Markdown", "示例", "博客"],
        "published_at": datetime.now(),
        "pinned": False,
        "is_draft": 0,
    },
]


# ============================================================================
# 前端配置数据（用于 --full 模式）
# ============================================================================
FRONTEND_SITE_SETTINGS = [
    {"key": "site_title", "value": "Firefly", "type": "string", "group": "basic", "label": "站点标题", "description": "网站的主标题", "sort_order": 100},
    {"key": "site_subtitle", "value": "Demo site", "type": "string", "group": "basic", "label": "站点副标题", "description": "网站的副标题", "sort_order": 99},
    {"key": "site_url", "value": "https://firefly.cuteleaf.cn", "type": "string", "group": "basic", "label": "站点URL", "description": "网站的完整URL地址", "sort_order": 98},
    {"key": "site_description", "value": "Firefly 是一款基于 Astro 框架和 Fuwari 模板开发的清新美观且现代化个人博客主题模板。", "type": "text", "group": "basic", "label": "站点描述", "description": "用于SEO的网站描述", "sort_order": 97},
    {"key": "site_keywords", "value": "Firefly,Fuwari,Astro,ACGN,博客,技术博客", "type": "string", "group": "basic", "label": "站点关键词", "description": "用于SEO的关键词", "sort_order": 96},
    {"key": "site_start_date", "value": "2025-01-01", "type": "string", "group": "basic", "label": "建站日期", "description": "网站创建日期", "sort_order": 94},
    {"key": "banner_title", "value": "Lovely firefly!", "type": "string", "group": "banner", "label": "横幅标题", "description": "主页横幅主标题", "sort_order": 99},
    {"key": "banner_subtitle", "value": '["In Reddened Chrysalis, I Once Rest","From Shattered Sky, I Free Fall","Amidst Silenced Stars, I Deep Sleep"]', "type": "json", "group": "banner", "label": "横幅副标题", "description": "副标题列表(JSON数组)", "sort_order": 98},
]

FRONTEND_SOCIAL_LINKS = [
    {"name": "GitHub", "icon": "fa6-brands:github", "url": "https://github.com/dear7575", "show_name": False, "sort_order": 100, "enabled": True},
    {"name": "Email", "icon": "fa6-solid:envelope", "url": "mailto:example@example.com", "show_name": False, "sort_order": 99, "enabled": True},
    {"name": "RSS", "icon": "fa6-solid:rss", "url": "/rss/", "show_name": False, "sort_order": 98, "enabled": True},
]

FRONTEND_FRIEND_LINKS = [
    {"title": "Firefly Docs", "avatar": "https://docs-firefly.cuteleaf.cn/logo.png", "description": "Firefly主题模板文档", "url": "https://docs-firefly.cuteleaf.cn", "tags": "Docs", "weight": 10, "enabled": True},
    {"title": "Astro", "avatar": "https://avatars.githubusercontent.com/u/44914786?v=4&s=640", "description": "The web framework for content-driven websites.", "url": "https://github.com/withastro/astro", "tags": "Framework", "weight": 9, "enabled": True},
]


# ============================================================================
# 初始化函数
# ============================================================================

def create_tables(drop_existing: bool = False):
    """创建数据库表"""
    if drop_existing:
        print("[WARNING] 删除现有表...")
        Base.metadata.drop_all(bind=engine)
        print("[OK] 现有表已删除")

    print("[INFO] 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据库表创建完成")


def init_admin(db):
    """初始化管理员账户"""
    admin = db.query(models.Admin).filter(models.Admin.username == "admin").first()
    if not admin:
        print("[INFO] 创建默认管理员账户...")
        new_admin = models.Admin(
            username="admin",
            hashed_password=get_password_hash("admin123")
        )
        db.add(new_admin)
        db.commit()
        print("[OK] 管理员账户创建完成")
        print("     用户名: admin")
        print("     密码: admin123")
        print("[WARNING] 请登录后立即修改默认密码！")
    else:
        print("[INFO] 管理员账户已存在，跳过...")


def init_site_settings(db, settings_data=None):
    """初始化站点设置"""
    if settings_data is None:
        settings_data = DEFAULT_SITE_SETTINGS

    print("[INFO] 初始化站点设置...")
    created_count = 0
    updated_count = 0

    for setting_data in settings_data:
        existing = db.query(models.SiteSetting).filter(
            models.SiteSetting.key == setting_data["key"]
        ).first()

        if not existing:
            db_setting = models.SiteSetting(**setting_data)
            db.add(db_setting)
            created_count += 1
        elif settings_data != DEFAULT_SITE_SETTINGS:
            # 仅在导入前端配置时更新现有值
            for k, v in setting_data.items():
                setattr(existing, k, v)
            updated_count += 1

    db.commit()
    print(f"[OK] 站点设置: 创建 {created_count} 条, 更新 {updated_count} 条")


def init_demo_categories(db):
    """初始化演示分类"""
    print("[INFO] 初始化演示分类...")
    created = 0
    category_map = {}

    for cat_data in DEMO_CATEGORIES:
        existing = db.query(models.Category).filter(
            models.Category.name == cat_data["name"]
        ).first()

        if not existing:
            db_cat = models.Category(**cat_data)
            db.add(db_cat)
            db.flush()
            category_map[cat_data["name"]] = db_cat
            created += 1
        else:
            category_map[cat_data["name"]] = existing

    db.commit()
    print(f"[OK] 分类: 创建 {created} 条")
    return category_map


def init_demo_tags(db):
    """初始化演示标签"""
    print("[INFO] 初始化演示标签...")
    created = 0
    tag_map = {}

    for tag_data in DEMO_TAGS:
        existing = db.query(models.Tag).filter(
            models.Tag.name == tag_data["name"]
        ).first()

        if not existing:
            db_tag = models.Tag(**tag_data)
            db.add(db_tag)
            db.flush()
            tag_map[tag_data["name"]] = db_tag
            created += 1
        else:
            tag_map[tag_data["name"]] = existing

    db.commit()
    print(f"[OK] 标签: 创建 {created} 条")
    return tag_map


def init_demo_posts(db, category_map, tag_map):
    """初始化演示文章"""
    print("[INFO] 初始化演示文章...")
    created = 0

    for post_data in DEMO_POSTS:
        existing = db.query(models.Post).filter(
            models.Post.slug == post_data["slug"]
        ).first()

        if existing:
            print(f"  [SKIP] 文章已存在: {post_data['title']}")
            continue

        # 获取分类
        category = category_map.get(post_data["category"])
        category_id = category.id if category else None

        # 创建文章
        db_post = models.Post(
            title=post_data["title"],
            slug=post_data["slug"],
            description=post_data["description"],
            content=post_data["content"],
            category_id=category_id,
            published_at=post_data["published_at"],
            pinned=post_data.get("pinned", False),
            is_draft=post_data.get("is_draft", 0),
        )
        db.add(db_post)
        db.flush()

        # 关联标签
        for tag_name in post_data.get("tags", []):
            tag = tag_map.get(tag_name)
            if tag:
                db_post.tags.append(tag)

        created += 1
        print(f"  [+] 创建文章: {post_data['title']}")

    db.commit()
    print(f"[OK] 文章: 创建 {created} 条")


def init_social_links(db, links_data=None):
    """初始化社交链接"""
    if links_data is None:
        return

    print("[INFO] 初始化社交链接...")
    created = 0

    for link_data in links_data:
        existing = db.query(models.SocialLink).filter(
            models.SocialLink.url == link_data["url"]
        ).first()

        if not existing:
            db_link = models.SocialLink(**link_data)
            db.add(db_link)
            created += 1

    db.commit()
    print(f"[OK] 社交链接: 创建 {created} 条")


def init_friend_links(db, friends_data=None):
    """初始化友情链接"""
    if friends_data is None:
        return

    print("[INFO] 初始化友情链接...")
    created = 0

    for friend_data in friends_data:
        existing = db.query(models.FriendLink).filter(
            models.FriendLink.url == friend_data["url"]
        ).first()

        if not existing:
            db_friend = models.FriendLink(**friend_data)
            db.add(db_friend)
            created += 1

    db.commit()
    print(f"[OK] 友情链接: 创建 {created} 条")


def print_statistics(db):
    """打印数据库统计信息"""
    print("\n" + "=" * 50)
    print("数据库统计信息:")
    print("-" * 50)
    print(f"  管理员: {db.query(models.Admin).count()} 条")
    print(f"  站点设置: {db.query(models.SiteSetting).count()} 条")
    print(f"  分类: {db.query(models.Category).count()} 条")
    print(f"  标签: {db.query(models.Tag).count()} 条")
    print(f"  文章: {db.query(models.Post).count()} 条")
    print(f"  社交链接: {db.query(models.SocialLink).count()} 条")
    print(f"  友情链接: {db.query(models.FriendLink).count()} 条")
    print("=" * 50)


# ============================================================================
# 静态文章导入功能
# ============================================================================

def parse_frontmatter(content: str) -> tuple:
    """解析 Markdown 文件的 frontmatter 和内容"""
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if match:
        frontmatter_str = match.group(1)
        body = match.group(2)
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
            return frontmatter, body
        except yaml.YAMLError as e:
            print(f"  YAML 解析错误: {e}")
            return {}, content

    return {}, content


def import_static_posts(db):
    """导入静态 Markdown 文章到数据库"""
    if not YAML_AVAILABLE:
        print("[ERROR] 需要安装 PyYAML: pip install pyyaml")
        return

    if not POSTS_DIR.exists():
        print(f"[ERROR] 文章目录不存在: {POSTS_DIR}")
        return

    print(f"[INFO] 扫描文章目录: {POSTS_DIR}")

    # 查找所有 Markdown 文件
    md_files = list(POSTS_DIR.glob("**/*.md"))
    print(f"[INFO] 找到 {len(md_files)} 个 Markdown 文件")

    imported_count = 0
    skipped_count = 0

    for md_file in md_files:
        # 跳过 .gitkeep 等特殊文件
        if md_file.name.startswith('.'):
            continue

        print(f"\n处理: {md_file.name}")

        # 读取文件内容
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析 frontmatter
        frontmatter, body = parse_frontmatter(content)

        if not frontmatter:
            print(f"  [SKIP] 无法解析 frontmatter")
            skipped_count += 1
            continue

        title = frontmatter.get("title", md_file.stem)
        slug = md_file.stem

        # 如果是 index.md，使用父目录名作为 slug
        if slug == "index":
            slug = md_file.parent.name

        # 检查是否已存在相同 slug 的文章
        existing = db.query(models.Post).filter(models.Post.slug == slug).first()
        if existing:
            print(f"  [SKIP] 文章 '{slug}' 已存在")
            skipped_count += 1
            continue

        # 处理分类
        category_name = frontmatter.get("category", "未分类")
        if isinstance(category_name, list):
            category_name = category_name[0] if category_name else "未分类"

        db_category = db.query(models.Category).filter(models.Category.name == category_name).first()
        if not db_category:
            db_category = models.Category(name=category_name)
            db.add(db_category)
            db.commit()
            db.refresh(db_category)
            print(f"  创建分类: {category_name}")

        # 处理发布时间
        published = frontmatter.get("published")
        if isinstance(published, str):
            try:
                published_at = datetime.fromisoformat(published)
            except:
                published_at = datetime.now()
        elif isinstance(published, datetime):
            published_at = published
        else:
            published_at = datetime.now()

        # 创建文章
        db_post = models.Post(
            title=title,
            slug=slug,
            description=frontmatter.get("description", ""),
            content=body.strip(),
            image=frontmatter.get("image", ""),
            category_id=db_category.id,
            is_draft=1 if frontmatter.get("draft", False) else 0,
            pinned=frontmatter.get("pinned", False),
            published_at=published_at
        )

        # 处理标签
        tags = frontmatter.get("tags", [])
        if isinstance(tags, list):
            for tag_name in tags:
                db_tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
                if not db_tag:
                    db_tag = models.Tag(name=tag_name)
                    db.add(db_tag)
                    db.commit()
                    db.refresh(db_tag)
                db_post.tags.append(db_tag)

        db.add(db_post)
        db.commit()

        print(f"  [+] 导入成功: {title}")
        imported_count += 1

    print(f"\n{'='*50}")
    print(f"静态文章导入完成!")
    print(f"  成功导入: {imported_count} 篇")
    print(f"  跳过: {skipped_count} 篇")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    # 解析命令行参数
    args = sys.argv[1:]
    reset_mode = "--reset" in args
    demo_mode = "--demo" in args
    full_mode = "--full" in args
    import_posts_mode = "--import-posts" in args

    print("=" * 60)
    print("Firefly CMS 数据库初始化")
    print("=" * 60)

    # 重置模式需要确认
    if reset_mode:
        confirm = input("[WARNING] 确定要删除所有数据吗？输入 'yes' 确认: ")
        if confirm.lower() != 'yes':
            print("[CANCELLED] 操作已取消")
            sys.exit(0)

    # 创建表
    create_tables(drop_existing=reset_mode)

    db = SessionLocal()
    try:
        # 基础初始化
        init_admin(db)
        init_site_settings(db)

        # 演示数据模式
        if demo_mode or full_mode:
            print("\n[INFO] 初始化演示数据...")
            category_map = init_demo_categories(db)
            tag_map = init_demo_tags(db)
            init_demo_posts(db, category_map, tag_map)

        # 完整模式：导入前端配置
        if full_mode:
            print("\n[INFO] 导入前端配置数据...")
            init_site_settings(db, FRONTEND_SITE_SETTINGS)
            init_social_links(db, FRONTEND_SOCIAL_LINKS)
            init_friend_links(db, FRONTEND_FRIEND_LINKS)

        # 导入静态文章模式
        if import_posts_mode:
            print("\n[INFO] 导入静态 Markdown 文章...")
            import_static_posts(db)

        # 打印统计信息
        print_statistics(db)

        print("\n[DONE] 数据库初始化完成!")
        print("\n后台管理地址: http://localhost:4321/admin/")
        print("默认账号: admin / admin123")

    finally:
        db.close()


if __name__ == "__main__":
    main()
