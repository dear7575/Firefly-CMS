"""
Firefly CMS API 主入口
FastAPI 应用程序配置和启动
"""
import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

import auth
import models
from database import engine, Base, get_db, SessionLocal, settings as db_settings
from routes import posts, categories, tags, friends, social, settings, dashboard, logs, search, upload, backup, analytics, auth as auth_routes, totp
from exception_handlers import register_exception_handlers
from logging_config import (
    setup_logging,
    set_request_id,
    reset_request_id,
    log_exception,
    get_logging_config_dict
)
from response_utils import build_error, normalize_payload, is_standard_payload
from rate_limiter import limiter, rate_limit_exceeded_handler, rate_limit_settings
from routes import posts, categories, tags, friends, social, settings, dashboard, logs, search, upload, backup, \
    analytics, auth as auth_routes, totp
from cache import set_cache_ttl_getter

setup_logging()
logger = logging.getLogger("firefly")

# 创建数据库表（如果不存在）
Base.metadata.create_all(bind=engine)

# 创建上传目录
os.makedirs(db_settings.UPLOAD_DIR, exist_ok=True)
# 创建备份目录
os.makedirs(db_settings.BACKUP_DIR, exist_ok=True)


def get_cache_ttl_from_db(cache_type: str) -> int:
    """从数据库读取缓存 TTL 配置"""
    key = f"cache_{cache_type}_ttl"
    db = SessionLocal()
    try:
        row = db.query(models.SiteSetting).filter(
            models.SiteSetting.key == key
        ).first()
        if row and row.value:
            return int(row.value)
    except Exception:
        pass
    finally:
        db.close()
    return 0


# 设置缓存 TTL 获取函数
set_cache_ttl_getter(get_cache_ttl_from_db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # === 启动时执行 ===
    stop_event = asyncio.Event()
    app.state.scheduled_publish_stop = stop_event
    app.state.scheduled_publish_task = asyncio.create_task(
        scheduled_publish_worker(stop_event)
    )

    if AUTO_BACKUP_ENABLED:
        backup_stop_event = asyncio.Event()
        app.state.auto_backup_stop = backup_stop_event
        app.state.auto_backup_task = asyncio.create_task(
            auto_backup_worker(backup_stop_event)
        )

    yield  # 应用运行中

    # === 关闭时执行 ===
    stop_event = getattr(app.state, "scheduled_publish_stop", None)
    task = getattr(app.state, "scheduled_publish_task", None)
    if stop_event:
        stop_event.set()
    if task:
        try:
            await task
        except asyncio.CancelledError:
            pass

    backup_stop = getattr(app.state, "auto_backup_stop", None)
    backup_task = getattr(app.state, "auto_backup_task", None)
    if backup_stop:
        backup_stop.set()
    if backup_task:
        try:
            await backup_task
        except asyncio.CancelledError:
            pass


# 创建 FastAPI 应用实例
app = FastAPI(
    title="Firefly CMS API",
    description="Firefly CMS 博客后台管理 API",
    version="2.0.0",
    lifespan=lifespan
)

# 注册全局异常处理器
register_exception_handlers(app)

# 注册 slowapi 速率限制
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# 解析 CORS 配置
def get_cors_config():
    """
    获取 CORS 中间件需要的配置

    当配置为 "*" 时，FastAPI 无法在 allow_credentials=True 的情况下返回通配符，
    因此默认放行常见的本地域名并通过正则动态匹配具体来源。
    """
    origins = (db_settings.CORS_ORIGINS or "").strip()
    if not origins or origins == "*":
        return {
            "allow_origins": [],
            "allow_origin_regex": r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
        }

    parsed_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
    return {
        "allow_origins": parsed_origins,
        "allow_origin_regex": None
    }


cors_config = get_cors_config()

# 配置 CORS 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_origin_regex=cors_config.get("allow_origin_regex"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（用于图片上传）
app.mount("/uploads", StaticFiles(directory=db_settings.UPLOAD_DIR), name="uploads")

# 定时发布后台任务（秒）
SCHEDULED_PUBLISH_INTERVAL = int(os.getenv("SCHEDULED_PUBLISH_INTERVAL", "60"))
if SCHEDULED_PUBLISH_INTERVAL < 10:
    SCHEDULED_PUBLISH_INTERVAL = 10

# 自动备份配置
AUTO_BACKUP_ENABLED = str(os.getenv("AUTO_BACKUP_ENABLED", str(db_settings.AUTO_BACKUP_ENABLED))).lower() in (
    "1", "true", "yes", "y", "on"
)
AUTO_BACKUP_INTERVAL_HOURS = int(os.getenv("AUTO_BACKUP_INTERVAL_HOURS", str(db_settings.AUTO_BACKUP_INTERVAL_HOURS)))
if AUTO_BACKUP_INTERVAL_HOURS < 1:
    AUTO_BACKUP_INTERVAL_HOURS = 1
AUTO_BACKUP_INTERVAL_SECONDS = AUTO_BACKUP_INTERVAL_HOURS * 3600


def read_backup_settings(db: Session) -> tuple[bool, int]:
    """读取自动备份设置（优先数据库，回退环境变量）"""
    enabled = AUTO_BACKUP_ENABLED
    interval_hours = AUTO_BACKUP_INTERVAL_HOURS

    rows = db.query(models.SiteSetting).filter(
        models.SiteSetting.key.in_(["backup_auto_enabled", "backup_auto_interval_hours"])
    ).all()
    for row in rows:
        if row.key == "backup_auto_enabled":
            value = (row.value or "").strip().lower()
            if value in ("true", "1", "yes", "y", "on"):
                enabled = True
            elif value in ("false", "0", "no", "n", "off"):
                enabled = False
        elif row.key == "backup_auto_interval_hours":
            try:
                interval_hours = int(float(row.value))
            except (TypeError, ValueError):
                interval_hours = AUTO_BACKUP_INTERVAL_HOURS

    if interval_hours < 1:
        interval_hours = 1

    return enabled, interval_hours


async def scheduled_publish_worker(stop_event: asyncio.Event):
    """后台循环处理定时发布文章"""
    logger.info("定时发布后台任务启动，间隔=%ss", SCHEDULED_PUBLISH_INTERVAL)
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                posts.process_scheduled_posts(db)
            finally:
                db.close()
        except Exception as exc:
            logger.error("定时发布处理失败: %s", exc)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=SCHEDULED_PUBLISH_INTERVAL)
        except asyncio.TimeoutError:
            continue


async def auto_backup_worker(stop_event: asyncio.Event):
    """后台循环执行自动备份"""
    logger.info("自动备份后台任务启动")

    # 首次启动时先等待，避免立即备份
    first_run = True

    while not stop_event.is_set():
        interval_hours = AUTO_BACKUP_INTERVAL_HOURS

        # 计算等待时间
        try:
            db = SessionLocal()
            try:
                enabled, interval_hours = read_backup_settings(db)
            finally:
                db.close()
        except Exception as exc:
            logger.error("读取备份配置失败: %s", exc)

        wait_seconds = AUTO_BACKUP_INTERVAL_SECONDS
        try:
            wait_seconds = interval_hours * 3600
        except Exception:
            wait_seconds = AUTO_BACKUP_INTERVAL_SECONDS

        # 先等待指定时间
        try:
            if first_run:
                logger.info("自动备份将在 %d 小时后首次执行", interval_hours)
                first_run = False
            await asyncio.wait_for(stop_event.wait(), timeout=wait_seconds)
        except asyncio.TimeoutError:
            # 等待时间到，执行备份
            try:
                db = SessionLocal()
                try:
                    enabled, _ = read_backup_settings(db)
                    if enabled:
                        logger.info("开始执行自动备份")
                        backup.create_backup_record(db, backup_type="full", source="auto")
                        logger.info("自动备份完成")
                    else:
                        logger.info("自动备份已关闭，跳过本次执行")
                finally:
                    db.close()
            except Exception as exc:
                logger.error("自动备份失败: %s", exc)


def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP 地址"""
    # 优先从代理头获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    # 直接连接的客户端 IP
    return request.client.host if request.client else "unknown"


def save_access_log(
        log_type: str,
        request: Request,
        username: str = None,
        status_code: int = None,
        detail: str = None
):
    """保存访问日志到数据库"""
    db = SessionLocal()
    try:
        log = models.AccessLog(
            log_type=log_type,
            username=username,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent", "")[:500],
            request_path=str(request.url.path),
            request_method=request.method,
            status_code=status_code,
            detail=detail,
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
    except Exception as e:
        log_exception(logger, "保存访问日志失败", e)
    finally:
        db.close()


@app.middleware("http")
async def standard_response_middleware(request: Request, call_next):
    """统一 API 响应格式为 code/msg/data"""
    response = await call_next(request)

    if not request.url.path.startswith("/api"):
        return response

    if response.status_code == status.HTTP_204_NO_CONTENT:
        return response

    if isinstance(response, StreamingResponse):
        return response

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type.lower():
        return response

    body = getattr(response, "body", None)
    if body is None:
        return response

    try:
        payload = json.loads(body)
    except Exception:
        return response

    if is_standard_payload(payload):
        return response

    normalized = normalize_payload(payload, request.method, response.status_code)
    new_response = JSONResponse(status_code=response.status_code, content=normalized)

    for key, value in response.headers.items():
        if key.lower() not in ("content-length", "content-type"):
            new_response.headers[key] = value

    return new_response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录写操作 API 请求的中间件（POST/PUT/DELETE）"""
    # 跳过静态资源和文档接口
    skip_paths = ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]
    if any(request.url.path.startswith(p) for p in skip_paths):
        return await call_next(request)

    # 执行请求
    response = await call_next(request)

    # 跳过登录接口（登录接口单独记录）
    if request.url.path == "/token":
        return response

    # 只记录写操作（POST/PUT/DELETE），忽略 GET 请求
    if request.method not in ["POST", "PUT", "DELETE"]:
        return response

    # 跳过日志相关接口（避免记录查看日志的操作）
    if request.url.path.startswith("/logs"):
        return response
    # 跳过主题色保存（避免产生大量日志）
    if request.url.path.endswith("/settings/by-key/theme_hue"):
        return response

    # 记录 API 访问日志
    # 从 Authorization 头提取用户名
    username = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            from database import settings as db_settings
            import jwt
            payload = jwt.decode(token, db_settings.SECRET_KEY, algorithms=[db_settings.ALGORITHM])
            username = payload.get("sub")
        except:
            pass

    save_access_log(
        log_type="api_access",
        request=request,
        username=username,
        status_code=response.status_code
    )

    return response


@app.middleware("http")
async def error_response_logger(request: Request, call_next):
    """记录所有 5xx 响应"""
    response = await call_next(request)
    if response.status_code >= 500 and not getattr(request.state, "error_logged", False):
        logger.error(
            "5xx 响应: %s %s status=%s",
            request.method,
            request.url.path,
            response.status_code
        )
        request.state.error_logged = True
    return response


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """为每个请求生成并透传 request_id"""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = set_request_id(request_id)
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    finally:
        reset_request_id(token)
    response.headers["X-Request-ID"] = request_id
    return response


# 创建 API 路由主入口
api_router = APIRouter(prefix="/api")

# 注册子路由到 API 路由
api_router.include_router(auth_routes.router)
api_router.include_router(posts.router)
api_router.include_router(categories.router)
api_router.include_router(tags.router)
api_router.include_router(friends.router)
api_router.include_router(social.router)
api_router.include_router(settings.router)
api_router.include_router(dashboard.router)
api_router.include_router(logs.router)
api_router.include_router(search.router)
api_router.include_router(upload.router)
api_router.include_router(backup.router)
api_router.include_router(analytics.router)
api_router.include_router(totp.router)


@api_router.post("/token", summary="用户登录", tags=["认证"])
@limiter.limit(rate_limit_settings.RATE_LIMIT_AUTH)
async def login(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    用户登录接口

    - **username**: 用户名
    - **password**: 密码

    如果用户启用了两步验证(2FA)，首次请求会返回 202 状态码，
    表示需要提供验证码。此时需要在请求头中添加：
    - X-TOTP-Code: 验证器App中的6位验证码
    - 或 X-Recovery-Code: 恢复码（8位）

    返回 JWT access_token 用于后续 API 认证
    """
    import pyotp
    import json

    # 查询用户
    user = db.query(models.Admin).filter(
        models.Admin.username == form_data.username
    ).first()

    # 验证用户名和密码
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        # 记录登录失败日志
        save_access_log(
            log_type="login_failed",
            request=request,
            username=form_data.username,
            status_code=401,
            detail="用户名或密码错误"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # === 2FA 两步验证检查 ===
    if user.totp_enabled and user.totp_verified:
        # 从请求头获取 TOTP 码或恢复码
        totp_code = request.headers.get("X-TOTP-Code")
        recovery_code = request.headers.get("X-Recovery-Code")

        if not totp_code and not recovery_code:
            # 需要 2FA 但未提供验证码，返回 202 表示需要继续验证
            return JSONResponse(
                status_code=202,
                content={
                    "code": 202,
                    "msg": "需要两步验证",
                    "data": {
                        "requires_2fa": True,
                        "username": user.username
                    }
                }
            )

        # 验证 TOTP 码
        if totp_code:
            totp_obj = pyotp.TOTP(user.totp_secret)
            if not totp_obj.verify(totp_code, valid_window=1):
                save_access_log(
                    log_type="login_failed",
                    request=request,
                    username=user.username,
                    status_code=401,
                    detail="2FA验证码错误"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="两步验证码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 防重放攻击：检查验证码是否已使用
            if user.last_totp_used == totp_code:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="验证码已使用，请等待新验证码",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user.last_totp_used = totp_code

        # 验证恢复码
        elif recovery_code:
            if not user.recovery_codes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="恢复码无效",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 验证并消费恢复码
            try:
                hashed_codes = json.loads(user.recovery_codes)
            except:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="恢复码验证失败",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            code_normalized = recovery_code.upper().replace("-", "").replace(" ", "")
            matched_index = -1
            for i, hashed in enumerate(hashed_codes):
                if auth.verify_password(code_normalized, hashed):
                    matched_index = i
                    break

            if matched_index == -1:
                save_access_log(
                    log_type="login_failed",
                    request=request,
                    username=user.username,
                    status_code=401,
                    detail="恢复码错误"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="恢复码错误或已使用",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 移除已使用的恢复码
            hashed_codes.pop(matched_index)
            user.recovery_codes = json.dumps(hashed_codes)

    # 记录登录成功日志
    save_access_log(
        log_type="login_success",
        request=request,
        username=user.username,
        status_code=200,
        detail="登录成功"
    )

    # 提交数据库更改（last_totp_used 或 recovery_codes）
    db.commit()

    # 生成访问令牌
    access_token = auth.create_access_token(data={"sub": user.username})
    return {
        "message": "登录成功",
        "access_token": access_token,
        "token_type": "bearer"
    }


@api_router.get("/", summary="API 根路径", tags=["系统"])
async def root():
    """
    API 根路径，返回欢迎信息
    """
    return {"message": "欢迎使用 Firefly CMS API", "version": "1.0.0"}


# 将 API 路由注册到 app
app.include_router(api_router)

# 直接运行此文件时启动服务器
if __name__ == "__main__":
    import uvicorn

    reload_env = os.getenv("APP_RELOAD")
    reload_enabled = True
    if reload_env is not None:
        reload_enabled = reload_env.strip().lower() in ("1", "true", "yes", "y", "on")

    proxy_headers_env = os.getenv("PROXY_HEADERS", "true")
    proxy_headers = proxy_headers_env.strip().lower() in ("1", "true", "yes", "y", "on")
    forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "*").strip()
    if not forwarded_allow_ips:
        forwarded_allow_ips = "*"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        log_config=get_logging_config_dict(),
        proxy_headers=proxy_headers,
        forwarded_allow_ips=forwarded_allow_ips,
        access_log=True
    )
