"""
异常处理器模块
提供全局异常处理函数
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError, ExpiredSignatureError

from exceptions import (
    APIException,
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    DatabaseError,
    ValidationError
)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    处理自定义 API 异常

    Args:
        request: FastAPI 请求对象
        exc: APIException 异常实例

    Returns:
        JSONResponse: 标准化的错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理 HTTP 异常

    Args:
        request: FastAPI 请求对象
        exc: HTTPException 异常实例

    Returns:
        JSONResponse: 标准化的错误响应
    """
    # 映射常见 HTTP 状态码到错误代码
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code_map.get(exc.status_code, "HTTP_ERROR"),
                "message": str(exc.detail)
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求验证异常

    Args:
        request: FastAPI 请求对象
        exc: RequestValidationError 异常实例

    Returns:
        JSONResponse: 标准化的错误响应，包含详细的验证错误信息
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求数据验证失败",
                "details": {
                    "errors": errors
                }
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    处理 SQLAlchemy 数据库异常

    Args:
        request: FastAPI 请求对象
        exc: SQLAlchemyError 异常实例

    Returns:
        JSONResponse: 标准化的错误响应
    """
    # 在生产环境中不应暴露详细的数据库错误信息
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "数据库操作失败，请稍后重试"
            }
        }
    )


async def jwt_exception_handler(request: Request, exc: JWTError) -> JSONResponse:
    """
    处理 JWT 相关异常

    Args:
        request: FastAPI 请求对象
        exc: JWTError 异常实例

    Returns:
        JSONResponse: 标准化的错误响应
    """
    if isinstance(exc, ExpiredSignatureError):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "认证信息已过期，请重新登录"
                }
            }
        )

    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "error": {
                "code": "INVALID_TOKEN",
                "message": "无效的认证信息"
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的通用异常

    Args:
        request: FastAPI 请求对象
        exc: Exception 异常实例

    Returns:
        JSONResponse: 标准化的错误响应
    """
    # 记录异常信息（生产环境应使用日志系统）
    print(f"未处理的异常: {type(exc).__name__}: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试"
            }
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from sqlalchemy.exc import SQLAlchemyError
    from jose import JWTError

    # 注册自定义异常处理器
    app.add_exception_handler(APIException, api_exception_handler)

    # 注册 HTTP 异常处理器
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # 注册验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # 注册数据库异常处理器
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # 注册 JWT 异常处理器
    app.add_exception_handler(JWTError, jwt_exception_handler)

    # 注册通用异常处理器（捕获所有未处理的异常）
    app.add_exception_handler(Exception, generic_exception_handler)
