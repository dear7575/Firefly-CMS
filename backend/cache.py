"""
简单的内存缓存模块
用于减少数据库查询压力，提升 API 响应速度
"""
import time
import threading
from typing import Any, Optional, Dict, Callable
from functools import wraps
import hashlib
import json

# 默认缓存时间配置（秒）
DEFAULT_CACHE_TTL = {
    "posts": 300,        # 文章缓存：5 分钟
    "categories": 600,   # 分类缓存：10 分钟
    "tags": 600,         # 标签缓存：10 分钟
    "settings": 1800,    # 设置缓存：30 分钟
    "frontend": 300,     # 前端缓存：5 分钟
}

# 缓存配置获取函数（延迟绑定，避免循环导入）
_get_cache_ttl_from_db: Optional[Callable[[str], int]] = None


def set_cache_ttl_getter(getter: Callable[[str], int]) -> None:
    """设置从数据库获取缓存 TTL 的函数"""
    global _get_cache_ttl_from_db
    _get_cache_ttl_from_db = getter


def get_cache_ttl(cache_type: str) -> int:
    """
    获取指定类型的缓存 TTL

    优先从数据库读取，失败则使用默认值
    """
    if _get_cache_ttl_from_db:
        try:
            ttl = _get_cache_ttl_from_db(cache_type)
            if ttl and ttl > 0:
                return ttl
        except Exception:
            pass
    return DEFAULT_CACHE_TTL.get(cache_type, 300)


class SimpleCache:
    """
    简单的内存缓存实现
    支持 TTL（过期时间）和手动清除
    """

    def __init__(self, default_ttl: int = 300):
        """
        初始化缓存

        Args:
            default_ttl: 默认缓存时间（秒），默认 5 分钟
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存的值，如果不存在或已过期则返回 None
        """
        with self._lock:
            if key not in self._cache:
                return None

            item = self._cache[key]
            if item['expires_at'] < time.time():
                # 缓存已过期，删除并返回 None
                del self._cache[key]
                return None

            return item['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 要缓存的值
            ttl: 过期时间（秒），如果不指定则使用默认值
        """
        with self._lock:
            expires_at = time.time() + (ttl if ttl is not None else self.default_ttl)
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }

    def delete(self, key: str) -> bool:
        """
        删除指定缓存

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存

        Args:
            pattern: 键的前缀模式

        Returns:
            删除的缓存数量
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    def clear(self) -> None:
        """清除所有缓存"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        清理所有过期的缓存

        Returns:
            清理的缓存数量
        """
        with self._lock:
            now = time.time()
            keys_to_delete = [
                k for k, v in self._cache.items()
                if v['expires_at'] < now
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含缓存统计的字典
        """
        with self._lock:
            now = time.time()
            total = len(self._cache)
            expired = sum(1 for v in self._cache.values() if v['expires_at'] < now)
            return {
                'total_keys': total,
                'expired_keys': expired,
                'active_keys': total - expired
            }


# 全局缓存实例
# 文章列表缓存：5 分钟
posts_cache = SimpleCache(default_ttl=300)

# 分类缓存：10 分钟
categories_cache = SimpleCache(default_ttl=600)

# 标签缓存：10 分钟
tags_cache = SimpleCache(default_ttl=600)

# 设置缓存：30 分钟
settings_cache = SimpleCache(default_ttl=1800)


def make_cache_key(*args, **kwargs) -> str:
    """
    根据参数生成缓存键

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键字符串
    """
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(cache: SimpleCache, key_prefix: str = '', ttl: Optional[int] = None):
    """
    缓存装饰器

    Args:
        cache: 缓存实例
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）

    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{make_cache_key(*args[1:], **kwargs)}" if key_prefix else make_cache_key(*args[1:], **kwargs)

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


def invalidate_posts_cache():
    """清除所有文章相关缓存"""
    posts_cache.clear()


def invalidate_categories_cache():
    """清除所有分类相关缓存"""
    categories_cache.clear()


def invalidate_tags_cache():
    """清除所有标签相关缓存"""
    tags_cache.clear()


def invalidate_settings_cache():
    """清除所有设置相关缓存"""
    settings_cache.clear()


def invalidate_all_cache():
    """清除所有缓存"""
    posts_cache.clear()
    categories_cache.clear()
    tags_cache.clear()
    settings_cache.clear()
