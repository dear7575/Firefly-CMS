"""
日志配置模块
提供统一日志配置、请求 ID 上下文与异常日志开关
支持按日期分割日志、自动清理过期日志
"""
from __future__ import annotations

import contextvars
import logging
import logging.config
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_request_id_var = contextvars.ContextVar("request_id", default="-")
_configured = False


class LogSettings(BaseSettings):
    """日志配置(从环境变量或 .env 读取)"""

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    # 日志保留天数
    LOG_RETENTION_DAYS: int = 30
    LOG_STACKTRACE: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


log_settings = LogSettings()


class RequestIdFilter(logging.Filter):
    """为日志记录注入 request_id 字段"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get("-")
        return True


class DailyRotatingFileHandler(TimedRotatingFileHandler):
    """
    按日期自动轮转的文件处理器
    - 每天午夜自动创建新日志文件
    - 自动清理过期日志
    """

    def __init__(self, log_dir: Path, log_type: str, retention_days: int = 30):
        """
        :param log_dir: 日志目录
        :param log_type: 日志类型 (app/access/error)
        :param retention_days: 日志保留天数
        """
        self.log_dir = log_dir
        self.log_type = log_type
        self.retention_days = retention_days

        log_dir.mkdir(parents=True, exist_ok=True)

        # 使用当前日期作为文件名
        filename = log_dir / f"{log_type}-{datetime.now().strftime('%Y-%m-%d')}.log"

        super().__init__(
            filename=str(filename),
            when='midnight',
            interval=1,
            backupCount=0,  # 我们手动管理清理
            encoding='utf-8',
            utc=False
        )

        # 设置日志文件名格式
        self.suffix = "%Y-%m-%d"

    def doRollover(self):
        """执行日志轮转并清理过期日志"""
        # 执行标准轮转
        super().doRollover()

        # 清理过期日志
        self.cleanup_old_logs()

    def cleanup_old_logs(self):
        """清理超过保留期的日志文件"""
        if self.retention_days <= 0:
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        # 遍历日志目录
        for log_file in self.log_dir.glob(f"{self.log_type}-*.log*"):
            try:
                # 从文件名提取日期
                parts = log_file.stem.split('-')
                if len(parts) >= 4:
                    date_str = '-'.join(parts[-3:])
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')

                    # 删除过期文件
                    if file_date < cutoff_date:
                        log_file.unlink()
                        logging.info(f"已清理过期日志: {log_file.name}")
            except (ValueError, IndexError):
                # 跳过无法解析日期的文件
                continue


def get_logging_config_dict() -> dict:
    """生成统一日志配置字典"""
    log_dir = Path(log_settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

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
            },
            "access": {
                "format": "%(asctime)s | %(request_id)s | %(message)s",
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
            "app_file": {
                "()": DailyRotatingFileHandler,
                "log_dir": log_dir,
                "log_type": "app",
                "retention_days": log_settings.LOG_RETENTION_DAYS,
                "level": log_settings.LOG_LEVEL,
                "formatter": "standard",
                "filters": ["request_id"]
            },
            "access_file": {
                "()": DailyRotatingFileHandler,
                "log_dir": log_dir,
                "log_type": "access",
                "retention_days": log_settings.LOG_RETENTION_DAYS,
                "level": "INFO",
                "formatter": "access",
                "filters": ["request_id"]
            },
            "error_file": {
                "()": DailyRotatingFileHandler,
                "log_dir": log_dir,
                "log_type": "error",
                "retention_days": log_settings.LOG_RETENTION_DAYS,
                "level": "ERROR",
                "formatter": "standard",
                "filters": ["request_id"]
            }
        },
        "root": {
            "level": log_settings.LOG_LEVEL,
            "handlers": ["console", "app_file", "error_file"]
        },
        "loggers": {
            "uvicorn": {
                "level": log_settings.LOG_LEVEL,
                "handlers": ["console", "app_file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "ERROR",
                "handlers": ["console", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False
            },
            "watchfiles": {
                "level": log_settings.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False
            }
        }
    }


def setup_logging() -> None:
    """初始化日志配置(幂等)"""
    global _configured
    if _configured:
        return

    logging.config.dictConfig(get_logging_config_dict())
    _configured = True

    # 启动时清理一次过期日志
    log_dir = Path(log_settings.LOG_DIR)
    if log_dir.exists():
        cleanup_all_old_logs()


def cleanup_all_old_logs():
    """清理所有类型的过期日志"""
    if log_settings.LOG_RETENTION_DAYS <= 0:
        return

    log_dir = Path(log_settings.LOG_DIR)
    cutoff_date = datetime.now() - timedelta(days=log_settings.LOG_RETENTION_DAYS)

    for log_type in ['app', 'access', 'error']:
        for log_file in log_dir.glob(f"{log_type}-*.log*"):
            try:
                parts = log_file.stem.split('-')
                if len(parts) >= 4:
                    date_str = '-'.join(parts[-3:])
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')

                    if file_date < cutoff_date:
                        log_file.unlink()
                        print(f"启动时清理过期日志: {log_file.name}")
            except (ValueError, IndexError):
                continue


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
