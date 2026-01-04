"""
日志配置模块
提供统一日志配置、请求 ID 上下文与异常日志开关
"""
from __future__ import annotations

import contextvars
import logging
import logging.config
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_request_id_var = contextvars.ContextVar("request_id", default="-")
_configured = False


class LogSettings(BaseSettings):
    """日志配置（从环境变量或 .env 读取）"""

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 7
    LOG_STACKTRACE: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


log_settings = LogSettings()


class RequestIdFilter(logging.Filter):
    """为日志记录注入 request_id 字段"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get("-")
        return True


def get_logging_config_dict() -> dict:
    """生成统一日志配置字典"""
    log_dir = Path(log_settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / log_settings.LOG_FILE

    handlers = ["console", "file"]

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {"()": RequestIdFilter}
        },
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_settings.LOG_LEVEL,
                "formatter": "standard",
                "filters": ["request_id"],
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_settings.LOG_LEVEL,
                "formatter": "standard",
                "filters": ["request_id"],
                "filename": str(log_file_path),
                "maxBytes": log_settings.LOG_MAX_BYTES,
                "backupCount": log_settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8"
            }
        },
        "root": {
            "level": log_settings.LOG_LEVEL,
            "handlers": handlers
        },
        "loggers": {
            "uvicorn": {
                "level": log_settings.LOG_LEVEL,
                "handlers": handlers,
                "propagate": False
            },
            "uvicorn.error": {
                "level": log_settings.LOG_LEVEL,
                "handlers": handlers,
                "propagate": False
            },
            "uvicorn.access": {
                "level": log_settings.LOG_LEVEL,
                "handlers": handlers,
                "propagate": False
            },
            "watchfiles": {
                "level": log_settings.LOG_LEVEL
            }
        }
    }


def setup_logging() -> None:
    """初始化日志配置（幂等）"""
    global _configured
    if _configured:
        return

    logging.config.dictConfig(get_logging_config_dict())
    _configured = True


def set_request_id(request_id: str):
    """设置当前请求的 request_id 上下文"""
    return _request_id_var.set(request_id)


def reset_request_id(token) -> None:
    """恢复 request_id 上下文"""
    _request_id_var.reset(token)


def should_log_stacktrace() -> bool:
    """是否输出异常堆栈"""
    return bool(log_settings.LOG_STACKTRACE)


def log_exception(logger: logging.Logger, message: str, exc: Exception) -> None:
    """按配置输出异常日志"""
    if should_log_stacktrace():
        logger.exception(message)
    else:
        logger.error("%s: %s", message, exc)
