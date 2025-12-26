"""
自定义异常模块
提供统一的异常类和错误响应格式
"""
from typing import Any, Dict, Optional


class APIException(Exception):
    """
    API 基础异常类

    所有自定义 API 异常都应继承此类
    """
    def __init__(
        self,
        message: str = "服务器内部错误",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        return result


# ============== 认证相关异常 ==============

class AuthenticationError(APIException):
    """认证失败异常"""
    def __init__(self, message: str = "认证失败", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class TokenExpiredError(APIException):
    """Token 过期异常"""
    def __init__(self, message: str = "认证信息已过期，请重新登录"):
        super().__init__(
            message=message,
            code="TOKEN_EXPIRED",
            status_code=401
        )


class InvalidTokenError(APIException):
    """无效 Token 异常"""
    def __init__(self, message: str = "无效的认证信息"):
        super().__init__(
            message=message,
            code="INVALID_TOKEN",
            status_code=401
        )


class PermissionDeniedError(APIException):
    """权限不足异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=403
        )


# ============== 资源相关异常 ==============

class NotFoundError(APIException):
    """资源不存在异常"""
    def __init__(self, resource: str = "资源", resource_id: str = None):
        message = f"{resource}不存在"
        details = {"resource_id": resource_id} if resource_id else None
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )


class AlreadyExistsError(APIException):
    """资源已存在异常"""
    def __init__(self, resource: str = "资源", field: str = None, value: str = None):
        message = f"{resource}已存在"
        details = {}
        if field:
            details["field"] = field
        if value:
            details["value"] = value
        super().__init__(
            message=message,
            code="ALREADY_EXISTS",
            status_code=409,
            details=details if details else None
        )


# ============== 请求相关异常 ==============

class ValidationError(APIException):
    """数据验证异常"""
    def __init__(self, message: str = "数据验证失败", errors: list = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors} if errors else None
        )


class BadRequestError(APIException):
    """错误请求异常"""
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400
        )


class RateLimitError(APIException):
    """频率限制异常"""
    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )


# ============== 文件相关异常 ==============

class FileTooLargeError(APIException):
    """文件过大异常"""
    def __init__(self, max_size_mb: int = 10):
        super().__init__(
            message=f"文件大小超过限制（最大 {max_size_mb}MB）",
            code="FILE_TOO_LARGE",
            status_code=413,
            details={"max_size_mb": max_size_mb}
        )


class InvalidFileTypeError(APIException):
    """无效文件类型异常"""
    def __init__(self, allowed_types: list = None):
        message = "不支持的文件类型"
        details = {"allowed_types": allowed_types} if allowed_types else None
        super().__init__(
            message=message,
            code="INVALID_FILE_TYPE",
            status_code=415,
            details=details
        )


# ============== 数据库相关异常 ==============

class DatabaseError(APIException):
    """数据库操作异常"""
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500
        )


class ConnectionError(APIException):
    """连接异常"""
    def __init__(self, service: str = "服务"):
        super().__init__(
            message=f"无法连接到{service}",
            code="CONNECTION_ERROR",
            status_code=503
        )
