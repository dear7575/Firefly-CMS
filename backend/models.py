from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean, Float, Date, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid
from database import Base

def generate_uuid():
    """生成 UUID 字符串"""
    return str(uuid.uuid4())

# 文章-标签 多对多关联表
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", String(36), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True, comment="文章ID"),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, comment="标签ID"),
    comment="文章标签关联表"
)

class Post(Base):
    """文章表"""
    __tablename__ = "posts"
    __table_args__ = {'comment': '文章表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="文章唯一标识(UUID)")
    title = Column(String(255), nullable=False, index=True, comment="文章标题")
    slug = Column(String(255), unique=True, nullable=False, index=True, comment="文章URL别名")
    description = Column(Text, nullable=True, comment="文章摘要描述")
    content = Column(LONGTEXT, nullable=False, comment="文章正文内容(Markdown)")
    image = Column(String(500), nullable=True, comment="文章封面图片URL")
    published_at = Column(DateTime, default=datetime.utcnow, comment="发布时间")
    category_id = Column(String(36), ForeignKey("categories.id"), comment="所属分类ID")
    is_draft = Column(Integer, default=0, comment="是否为草稿(0:否, 1:是)")
    pinned = Column(Boolean, default=False, index=True, comment="是否置顶")
    pin_order = Column(Integer, default=0, index=True, comment="置顶排序(数字越小越靠前)")
    password = Column(String(255), nullable=True, comment="文章访问密码(明文,可选)")
    status = Column(String(20), default="draft", index=True, comment="发布状态(draft/published/scheduled)")
    scheduled_at = Column(DateTime, nullable=True, comment="定时发布时间")
    autosave_data = Column(LONGTEXT, nullable=True, comment="自动保存内容(JSON)")
    autosave_at = Column(DateTime, nullable=True, comment="自动保存时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最后更新时间")
    deleted_at = Column(DateTime, nullable=True, index=True, comment="软删除时间(NULL表示未删除)")

    category = relationship("Category", back_populates="posts")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")
    media_files = relationship(
        "MediaFile",
        secondary="post_media",
        back_populates="posts"
    )
    view_stats = relationship(
        "PostViewStat",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    revisions = relationship(
        "PostRevision",
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="desc(PostRevision.created_at)"
    )


class PostRevision(Base):
    """文章版本记录"""
    __tablename__ = "post_revisions"
    __table_args__ = {'comment': '文章版本历史'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="版本ID(UUID)")
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True, comment="文章ID")
    title = Column(String(255), nullable=False, comment="版本标题")
    slug = Column(String(255), nullable=False, comment="版本Slug")
    description = Column(Text, nullable=True, comment="版本摘要")
    content = Column(LONGTEXT, nullable=False, comment="版本内容")
    editor = Column(String(50), nullable=True, comment="编辑者用户名")
    created_at = Column(DateTime, default=datetime.utcnow, comment="版本创建时间")

    post = relationship("Post", back_populates="revisions")


class MediaFile(Base):
    """媒体文件表"""
    __tablename__ = "media_files"
    __table_args__ = {'comment': '媒体文件元数据'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="媒体ID(UUID)")
    filename = Column(String(255), nullable=False, comment="存储文件名")
    original_name = Column(String(255), nullable=True, comment="原始文件名")
    mime_type = Column(String(100), nullable=True, comment="文件类型")
    size = Column(Integer, default=0, comment="文件大小(字节)")
    url = Column(String(500), nullable=False, comment="访问 URL")
    path = Column(String(500), nullable=False, comment="服务器路径")
    uploader = Column(String(50), nullable=True, comment="上传者用户名")
    width = Column(Integer, nullable=True, comment="图片宽度")
    height = Column(Integer, nullable=True, comment="图片高度")
    usage_count = Column(Integer, default=0, comment="引用次数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="上传时间")

    posts = relationship(
        "Post",
        secondary="post_media",
        back_populates="media_files"
    )


class PostMedia(Base):
    """文章与媒体关联表"""
    __tablename__ = "post_media"
    __table_args__ = {'comment': '文章与媒体文件关联'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="关联ID")
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True, comment="文章ID")
    media_id = Column(String(36), ForeignKey("media_files.id", ondelete="CASCADE"), nullable=False, index=True, comment="媒体ID")
    context = Column(String(100), nullable=True, comment="使用场景")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class PostViewStat(Base):
    """文章访问统计（按日聚合）"""
    __tablename__ = "post_view_stats"
    __table_args__ = {'comment': '文章访问统计表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="统计ID")
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False, comment="文章ID")
    date = Column(Date, default=date.today, index=True, nullable=False, comment="统计日期")
    views = Column(Integer, default=0, comment="浏览次数")
    unique_views = Column(Integer, default=0, comment="访客数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="记录创建时间")

    post = relationship("Post", back_populates="view_stats")


class PostViewClient(Base):
    """文章访问唯一访客记录"""
    __tablename__ = "post_view_clients"
    __table_args__ = (
        UniqueConstraint("post_id", "date", "client_hash", name="uq_post_client_date"),
        {'comment': '文章访问客户端记录'}
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="记录ID")
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True, comment="文章ID")
    date = Column(Date, default=date.today, nullable=False, index=True, comment="日期")
    client_hash = Column(String(64), nullable=False, index=True, comment="客户端哈希")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

class Category(Base):
    """分类表"""
    __tablename__ = "categories"
    __table_args__ = {'comment': '文章分类表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="分类ID(UUID)")
    name = Column(String(50), unique=True, nullable=False, index=True, comment="分类名称")
    slug = Column(String(50), unique=True, nullable=True, index=True, comment="分类URL别名")
    description = Column(Text, nullable=True, comment="分类描述")
    icon = Column(String(100), nullable=True, comment="分类图标(iconify格式)")
    color = Column(String(20), nullable=True, comment="分类颜色(HEX)")
    sort_order = Column(Integer, default=0, comment="排序权重(越大越靠前)")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    posts = relationship("Post", back_populates="category")

class Tag(Base):
    """标签表"""
    __tablename__ = "tags"
    __table_args__ = {'comment': '文章标签表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="标签ID(UUID)")
    name = Column(String(50), unique=True, nullable=False, index=True, comment="标签名称")
    slug = Column(String(50), unique=True, nullable=True, index=True, comment="标签URL别名")
    color = Column(String(20), nullable=True, comment="标签颜色(HEX)")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    posts = relationship("Post", secondary=post_tags, back_populates="tags")

class Admin(Base):
    """管理员表"""
    __tablename__ = "admins"
    __table_args__ = {'comment': '管理员账户表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="管理员ID(UUID)")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="登录用户名")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希值(PBKDF2)")


class FriendLink(Base):
    """友情链接表"""
    __tablename__ = "friend_links"
    __table_args__ = {'comment': '友情链接表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="链接ID(UUID)")
    title = Column(String(100), nullable=False, comment="网站名称")
    url = Column(String(500), nullable=False, comment="网站URL")
    avatar = Column(String(500), nullable=True, comment="网站头像/Logo URL")
    description = Column(Text, nullable=True, comment="网站描述")
    tags = Column(String(200), nullable=True, comment="标签(逗号分隔)")
    weight = Column(Integer, default=0, comment="排序权重(越大越靠前)")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class SocialLink(Base):
    """社交链接表"""
    __tablename__ = "social_links"
    __table_args__ = {'comment': '社交链接表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="链接ID(UUID)")
    name = Column(String(50), nullable=False, comment="平台名称")
    icon = Column(String(100), nullable=False, comment="图标(iconify格式)")
    url = Column(String(500), nullable=False, comment="链接URL")
    show_name = Column(Boolean, default=False, comment="是否显示名称")
    sort_order = Column(Integer, default=0, comment="排序权重(越大越靠前)")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class SiteSetting(Base):
    """站点设置表(Key-Value存储)"""
    __tablename__ = "site_settings"
    __table_args__ = {'comment': '站点设置表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="设置ID(UUID)")
    key = Column(String(100), unique=True, nullable=False, index=True, comment="设置键名")
    value = Column(Text, nullable=True, comment="设置值")
    type = Column(String(20), default="string", comment="值类型(string/number/boolean/json)")
    group = Column(String(50), default="general", comment="设置分组")
    label = Column(String(100), nullable=True, comment="显示标签")
    description = Column(Text, nullable=True, comment="设置描述")
    sort_order = Column(Integer, default=0, comment="排序权重")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class AccessLog(Base):
    """访问日志表"""
    __tablename__ = "access_logs"
    __table_args__ = {'comment': '访问日志表'}

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True, comment="日志ID(UUID)")
    log_type = Column(String(50), nullable=False, index=True, comment="日志类型(login_success/login_failed/api_access)")
    username = Column(String(100), nullable=True, index=True, comment="用户名")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="客户端User-Agent")
    request_path = Column(String(200), nullable=True, index=True, comment="请求路径")
    request_method = Column(String(10), nullable=True, comment="请求方法")
    status_code = Column(Integer, nullable=True, comment="响应状态码")
    detail = Column(Text, nullable=True, comment="详细信息")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")
