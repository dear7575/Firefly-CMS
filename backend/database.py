"""
数据库配置模块
提供数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
import secrets


class Settings(BaseSettings):
    """
    应用配置类

    配置项可通过环境变量或 .env 文件覆盖
    """
    # 数据库连接字符串
    # 格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
    # 重要：生产环境请使用 .env 文件配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@192.168.0.66:3306/firefly_blog"

    # JWT 密钥
    # 重要：生产环境请更换为随机生成的密钥
    # 可使用命令生成: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "your-secret-key-for-jwt-please-change-in-production"

    # JWT 加密算法
    ALGORITHM: str = "HS256"

    # Token 过期时间（分钟）
    # 默认 1440 分钟 = 24 小时
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    class Config:
        # 从 .env 文件加载配置
        env_file = ".env"


# 创建全局配置实例
settings = Settings()

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
