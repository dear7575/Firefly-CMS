"""
API 速率限制配置模块
使用 slowapi 实现基于 IP 的速率限制
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class RateLimitSettings(BaseSettings):
    """速率限制配置"""

    # 是否启用速率限制
    RATE_LIMIT_ENABLED: bool = True

    # 默认限制 (每分钟请求数)
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # 登录接口限制 (更严格)
    RATE_LIMIT_AUTH: str = "5/minute"

    # 上传接口限制
    RATE_LIMIT_UPLOAD: str = "10/minute"

    # 白名单 IP (逗号分隔)
    RATE_LIMIT_WHITELIST: str = "127.0.0.1,localhost"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


rate_limit_settings = RateLimitSettings()


def get_real_client_ip(request: Request) -> str:
    """获取客户端真实 IP 地址 (支持代理)"""
    # 优先从代理头获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    # 直接连接的客户端 IP
    return request.client.host if request.client else "unknown"


def check_whitelist(request: Request) -> str:
    """检查 IP 是否在白名单中,白名单 IP 返回固定 key 以跳过限制"""
    client_ip = get_real_client_ip(request)
    whitelist = [ip.strip() for ip in rate_limit_settings.RATE_LIMIT_WHITELIST.split(",")]

    if client_ip in whitelist:
        # 返回一个不会被限制的固定 key
        return "__whitelist__"
    return client_ip


# 创建限流器实例
limiter = Limiter(
    key_func=check_whitelist,
    default_limits=[rate_limit_settings.RATE_LIMIT_DEFAULT] if rate_limit_settings.RATE_LIMIT_ENABLED else [],
    enabled=rate_limit_settings.RATE_LIMIT_ENABLED,
    storage_uri="memory://"  # 使用内存存储,生产环境可改为 Redis
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """速率限制超出时的处理器"""
    client_ip = get_real_client_ip(request)
    logger.warning(f"速率限制触发: IP={client_ip}, 路径={request.url.path}")

    return JSONResponse(
        status_code=429,
        content={
            "code": 429,
            "msg": "请求过于频繁",
            "data": {
                "error": "RATE_LIMIT_EXCEEDED",
                "message": f"您的请求速度过快,请稍后再试。限制: {exc.detail}",
                "retry_after": 60
            }
        },
        headers={
            "Retry-After": "60"
        }
    )
