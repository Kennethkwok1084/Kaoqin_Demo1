"""
Redis缓存服务
提供统计数据缓存和高性能数据访问
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理类"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False

        # 缓存配置
        self.default_ttl = 3600  # 默认1小时过期
        self.stats_ttl = 1800  # 统计数据30分钟过期
        self.long_cache_ttl = 86400  # 长期缓存24小时过期

        # 缓存键前缀
        self.key_prefix = "attendance_system:"
        self.stats_prefix = f"{self.key_prefix}stats:"
        self.member_prefix = f"{self.key_prefix}member:"
        self.task_prefix = f"{self.key_prefix}task:"

    async def connect(self):
        """连接Redis"""
        try:
            if not settings.REDIS_URL:
                logger.warning("Redis URL not configured, cache will be disabled")
                return

            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # 测试连接
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Redis connection established")

        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis: {str(e)}. Cache will be disabled."
            )
            self.is_connected = False
            self.redis_client = None

    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Redis connection closed")

    def _generate_cache_key(self, key_type: str, **kwargs) -> str:
        """生成缓存键"""
        # 根据参数生成唯一的缓存键
        param_string = "_".join(
            f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None
        )

        if param_string:
            # 对长参数字符串进行哈希
            if len(param_string) > 100:
                param_hash = hashlib.md5(param_string.encode()).hexdigest()[:8]
                param_string = f"hash_{param_hash}"

            return f"{key_type}{param_string}"
        else:
            return key_type

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if not self.is_connected or not self.redis_client:
            return None

        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存数据"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            ttl = ttl or self.default_ttl
            data = json.dumps(value, default=str, ensure_ascii=False)
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存数据"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存数据"""
        if not self.is_connected or not self.redis_client:
            return 0

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Deleted {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.warning(
                f"Cache delete pattern error for pattern {pattern}: {str(e)}"
            )
            return 0

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def get_ttl(self, key: str) -> int:
        """获取缓存剩余过期时间"""
        if not self.is_connected or not self.redis_client:
            return -1

        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.warning(f"Cache TTL error for key {key}: {str(e)}")
            return -1

    # 统计数据缓存方法

    async def get_stats_cache(
        self, cache_type: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """获取统计数据缓存"""
        cache_key = self._generate_cache_key(
            f"{self.stats_prefix}{cache_type}:", **kwargs
        )
        return await self.get(cache_key)

    async def set_stats_cache(
        self, cache_type: str, data: Dict[str, Any], ttl: Optional[int] = None, **kwargs
    ) -> bool:
        """设置统计数据缓存"""
        cache_key = self._generate_cache_key(
            f"{self.stats_prefix}{cache_type}:", **kwargs
        )
        ttl = ttl or self.stats_ttl

        # 添加缓存时间戳
        data_with_meta = {
            "data": data,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_key": cache_key,
        }

        success = await self.set(cache_key, data_with_meta, ttl)
        if success:
            logger.debug(f"Stats cache set: {cache_key} (TTL: {ttl}s)")
        return success

    async def invalidate_stats_cache(self, cache_type: Optional[str] = None) -> int:
        """清除统计数据缓存"""
        if cache_type:
            pattern = f"{self.stats_prefix}{cache_type}:*"
        else:
            pattern = f"{self.stats_prefix}*"

        deleted = await self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} stats cache entries")
        return deleted

    # 成员数据缓存方法

    async def get_member_cache(
        self, member_id: int, cache_type: str = "profile"
    ) -> Optional[Dict[str, Any]]:
        """获取成员数据缓存"""
        cache_key = f"{self.member_prefix}{member_id}:{cache_type}"
        return await self.get(cache_key)

    async def set_member_cache(
        self,
        member_id: int,
        data: Dict[str, Any],
        cache_type: str = "profile",
        ttl: Optional[int] = None,
    ) -> bool:
        """设置成员数据缓存"""
        cache_key = f"{self.member_prefix}{member_id}:{cache_type}"
        ttl = ttl or self.default_ttl
        return await self.set(cache_key, data, ttl)

    async def invalidate_member_cache(self, member_id: Optional[int] = None) -> int:
        """清除成员数据缓存"""
        if member_id:
            pattern = f"{self.member_prefix}{member_id}:*"
        else:
            pattern = f"{self.member_prefix}*"

        return await self.delete_pattern(pattern)

    # 任务数据缓存方法

    async def get_task_cache(
        self, cache_type: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """获取任务数据缓存"""
        cache_key = self._generate_cache_key(
            f"{self.task_prefix}{cache_type}:", **kwargs
        )
        return await self.get(cache_key)

    async def set_task_cache(
        self, cache_type: str, data: Dict[str, Any], ttl: Optional[int] = None, **kwargs
    ) -> bool:
        """设置任务数据缓存"""
        cache_key = self._generate_cache_key(
            f"{self.task_prefix}{cache_type}:", **kwargs
        )
        ttl = ttl or self.default_ttl
        return await self.set(cache_key, data, ttl)

    async def invalidate_task_cache(self, cache_type: Optional[str] = None) -> int:
        """清除任务数据缓存"""
        if cache_type:
            pattern = f"{self.task_prefix}{cache_type}:*"
        else:
            pattern = f"{self.task_prefix}*"

        return await self.delete_pattern(pattern)

    # 批量操作方法

    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存数据"""
        if not self.is_connected or not self.redis_client or not keys:
            return {}

        try:
            values = await self.redis_client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = None
                else:
                    result[key] = None

            return result
        except Exception as e:
            logger.warning(f"Cache mget error: {str(e)}")
            return {}

    async def set_multiple(
        self, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """批量设置缓存数据"""
        if not self.is_connected or not self.redis_client or not data:
            return False

        try:
            ttl = ttl or self.default_ttl
            pipe = self.redis_client.pipeline()

            for key, value in data.items():
                json_data = json.dumps(value, default=str, ensure_ascii=False)
                pipe.setex(key, ttl, json_data)

            await pipe.execute()
            return True
        except Exception as e:
            logger.warning(f"Cache mset error: {str(e)}")
            return False

    # 缓存装饰器支持方法

    async def cache_or_compute(
        self, key: str, compute_func, ttl: Optional[int] = None, *args, **kwargs
    ) -> Any:
        """缓存或计算数据"""
        # 先尝试从缓存获取
        cached_data = await self.get(key)
        if cached_data is not None:
            logger.debug(f"Cache hit: {key}")
            return cached_data

        # 缓存未命中，计算数据
        logger.debug(f"Cache miss: {key}")
        computed_data = await compute_func(*args, **kwargs)

        # 将计算结果存入缓存
        if computed_data is not None:
            await self.set(key, computed_data, ttl)

        return computed_data

    # 健康检查方法

    async def health_check(self) -> Dict[str, Any]:
        """Redis健康检查"""
        health_info = {
            "connected": self.is_connected,
            "redis_url": settings.REDIS_URL is not None,
            "info": None,
            "memory_usage": None,
            "keyspace_info": None,
        }

        if self.is_connected and self.redis_client:
            try:
                # 获取Redis信息
                info = await self.redis_client.info()
                health_info["info"] = {
                    "version": info.get("redis_version"),
                    "mode": info.get("redis_mode"),
                    "role": info.get("role"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "uptime_in_seconds": info.get("uptime_in_seconds"),
                }

                # 获取内存使用情况
                memory_info = await self.redis_client.info("memory")
                health_info["memory_usage"] = {
                    "used_memory": memory_info.get("used_memory"),
                    "used_memory_human": memory_info.get("used_memory_human"),
                    "used_memory_peak": memory_info.get("used_memory_peak"),
                    "used_memory_peak_human": memory_info.get("used_memory_peak_human"),
                    "mem_fragmentation_ratio": memory_info.get(
                        "mem_fragmentation_ratio"
                    ),
                }

                # 获取键空间信息
                keyspace_info = await self.redis_client.info("keyspace")
                health_info["keyspace_info"] = keyspace_info

            except Exception as e:
                health_info["error"] = str(e)
                logger.warning(f"Redis health check error: {str(e)}")

        return health_info


# 全局缓存实例
cache = RedisCache()


# 缓存装饰器
def cached(key_pattern: str, ttl: int = 3600, cache_type: str = "general"):
    """
    缓存装饰器

    Args:
        key_pattern: 缓存键模式，支持格式化参数
        ttl: 过期时间（秒）
        cache_type: 缓存类型
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            try:
                cache_key = key_pattern.format(*args, **kwargs)
            except (KeyError, IndexError):
                # 如果格式化失败，使用函数名和参数哈希
                param_hash = hashlib.md5(
                    str(args + tuple(kwargs.items())).encode()
                ).hexdigest()[:8]
                cache_key = f"{cache.key_prefix}{func.__name__}:{param_hash}"

            return await cache.cache_or_compute(cache_key, func, ttl, *args, **kwargs)

        return wrapper

    return decorator


# 缓存失效装饰器
def invalidate_cache(patterns: List[str]):
    """
    缓存失效装饰器

    Args:
        patterns: 要失效的缓存模式列表
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # 执行成功后失效相关缓存
            for pattern in patterns:
                try:
                    formatted_pattern = pattern.format(*args, **kwargs)
                    await cache.delete_pattern(formatted_pattern)
                except (KeyError, IndexError):
                    logger.warning(
                        f"Failed to format cache invalidation pattern: {pattern}"
                    )

            return result

        return wrapper

    return decorator


# 初始化和清理函数
async def init_cache():
    """初始化缓存连接"""
    await cache.connect()


async def cleanup_cache():
    """清理缓存连接"""
    await cache.disconnect()
