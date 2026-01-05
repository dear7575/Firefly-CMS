"""
数据库配置模块
提供数据库连接和会话管理
"""
import os
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 默认不安全的密钥标识
DEFAULT_INSECURE_KEY = "your-secret-key-for-jwt-please-change-in-production"


def get_or_create_secret_key() -> str:
    """
    获取或创建安全的 SECRET_KEY

    优先级：
    1. 环境变量 SECRET_KEY
    2. .env 文件中的 SECRET_KEY
    3. 自动生成并保存到 .env 文件

    Returns:
        str: 安全的 SECRET_KEY
    """
    # 检查环境变量
    env_key = os.environ.get("SECRET_KEY")
    if env_key and env_key != DEFAULT_INSECURE_KEY:
        return env_key

    # 检查 .env 文件
    env_file = ".env"
    existing_key = None
    env_lines = []

    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            env_lines = f.readlines()
            for line in env_lines:
                if line.strip().startswith("SECRET_KEY="):
                    existing_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    # 如果已有安全的密钥，直接返回
    if existing_key and existing_key != DEFAULT_INSECURE_KEY:
        return existing_key

    # 生成新的安全密钥
    new_key = secrets.token_hex(32)

    # 更新或添加到 .env 文件
    key_found = False
    new_lines = []
    for line in env_lines:
        if line.strip().startswith("SECRET_KEY="):
            new_lines.append(f'SECRET_KEY="{new_key}"\n')
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:
        # 添加注释和新密钥
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append("\n# JWT 安全密钥 (自动生成，请勿泄露)\n")
        new_lines.append(f'SECRET_KEY="{new_key}"\n')

    # 写入文件
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"[安全] 已自动生成 JWT SECRET_KEY 并保存到 {env_file}")

    return new_key


class Settings(BaseSettings):
    """
    应用配置类

    配置项可通过环境变量或 .env 文件覆盖
    """
    # 数据库连接字符串
    # 格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
    # 重要：生产环境请使用 .env 文件配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@127.0.0.1:3306/firefly_cms"

    # JWT 密钥 - 将在初始化后被安全密钥替换
    SECRET_KEY: str = DEFAULT_INSECURE_KEY

    # JWT 加密算法
    ALGORITHM: str = "HS256"

    # Token 过期时间（分钟）
    # 默认 1440 分钟 = 24 小时
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS 允许的域名列表（逗号分隔）
    # 生产环境请设置为具体域名，如: "https://yourdomain.com,https://admin.yourdomain.com"
    # 设置为 "*" 表示允许所有域名（仅用于开发环境）
    CORS_ORIGINS: str = "*"

    # 上传文件存储路径
    UPLOAD_DIR: str = "uploads"

    # 最大上传文件大小（MB）
    MAX_UPLOAD_SIZE: int = 10

    # API 频率限制（每分钟请求数）
    # 开发环境建议设置较大值，生产环境可根据实际情况调整
    RATE_LIMIT_PER_MINUTE: int = 500

    # 系统日志配置
    # 日志等级
    LOG_LEVEL: str = "INFO"
    # 日志堆栈跟踪
    LOG_STACKTRACE: bool = True
    # 日志目录
    LOG_DIR: str = "logs"
    # 日志文件名称
    LOG_FILE: str = "app.log"
    # 日志最大小
    LOG_MAX_BYTES: int = 10485760
    # 日志备份天数
    LOG_BACKUP_COUNT: int = 7

    # 从 .env 文件加载配置，并忽略不属于本模型的字段
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# 创建全局配置实例
settings = Settings()

# 确保使用安全的 SECRET_KEY
if settings.SECRET_KEY == DEFAULT_INSECURE_KEY:
    settings.SECRET_KEY = get_or_create_secret_key()
    print("[安全] JWT SECRET_KEY 已更新为安全密钥")

# 创建数据库引擎
engine = create_engine(settings.DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖注入函数

    使用方式:
        @app.get("/")
        def read_items(db: Session = Depends(get_db)):
            ...

    Yields:
        Session: SQLAlchemy 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
