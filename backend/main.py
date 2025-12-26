"""
Firefly Blog API 主入口
FastAPI 应用程序配置和启动
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
import time
import os

import auth
import models
from database import engine, Base, get_db, SessionLocal, settings as db_settings
from routes import posts, categories, tags, friends, social, settings, dashboard, logs, search, upload, backup
from exception_handlers import register_exception_handlers
from exceptions import RateLimitError

# 创建数据库表（如果不存在）
Base.metadata.create_all(bind=engine)

# 创建上传目录
os.makedirs(db_settings.UPLOAD_DIR, exist_ok=True)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Firefly Blog API",
    description="Firefly 博客后台管理 API",
    version="2.0.0"
)

# 注册全局异常处理器
register_exception_handlers(app)

# 解析 CORS 允许的域名
def get_cors_origins():
    """从配置获取 CORS 允许的域名列表"""
    origins = db_settings.CORS_ORIGINS
    if origins == "*":
        return ["*"]
    return [origin.strip() for origin in origins.split(",") if origin.strip()]

# 配置 CORS 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（用于图片上传）
app.mount("/uploads", StaticFiles(directory=db_settings.UPLOAD_DIR), name="uploads")

# API 频率限制存储
rate_limit_store = defaultdict(list)


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


def check_rate_limit(client_ip: str) -> bool:
    """检查 API 频率限制"""
    current_time = time.time()
    window_start = current_time - 60  # 1分钟窗口

    # 清理过期记录
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if t > window_start
    ]

    # 检查是否超过限制
    if len(rate_limit_store[client_ip]) >= db_settings.RATE_LIMIT_PER_MINUTE:
        return False

    # 记录本次请求
    rate_limit_store[client_ip].append(current_time)
    return True


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
        print(f"保存日志失败: {e}")
    finally:
        db.close()


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """API 频率限制中间件"""
    # 跳过静态资源
    if request.url.path.startswith("/uploads") or request.url.path.startswith("/docs"):
        return await call_next(request)

    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        # 使用统一的错误响应格式
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "请求过于频繁，请稍后再试"
                }
            }
        )
    return await call_next(request)


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


# 注册路由
app.include_router(posts.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(friends.router)
app.include_router(social.router)
app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(logs.router)
app.include_router(search.router)
app.include_router(upload.router)
app.include_router(backup.router)


@app.post("/token", summary="用户登录", tags=["认证"])
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录接口

    - **username**: 用户名
    - **password**: 密码

    返回 JWT access_token 用于后续 API 认证
    """
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

    # 记录登录成功日志
    save_access_log(
        log_type="login_success",
        request=request,
        username=user.username,
        status_code=200,
        detail="登录成功"
    )

    # 生成访问令牌
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/", summary="API 根路径", tags=["系统"])
async def root():
    """
    API 根路径，返回欢迎信息
    """
    return {"message": "欢迎使用 Firefly 博客 API", "version": "1.0.0"}


# 直接运行此文件时启动服务器
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
