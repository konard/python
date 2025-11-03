"""
Redis-based caching layer for YouTube API responses.
"""
import json
from typing import Any, Optional
import logging

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class YouTubeCache:
    """
    Redis-based cache for YouTube API responses.
    Reduces API calls and improves performance.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache.

        Args:
            redis_url: Redis connection URL (defaults to settings)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[aioredis.Redis] = None
        self.prefix = "youtube:cache:"

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self.redis

    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        redis = await self._get_redis()
        full_key = f"{self.prefix}{key}"

        try:
            value = await redis.get(full_key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set cached value with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        redis = await self._get_redis()
        full_key = f"{self.prefix}{key}"

        try:
            serialized = json.dumps(value)
            if ttl:
                await redis.setex(full_key, ttl, serialized)
            else:
                await redis.set(full_key, serialized)

            logger.debug(f"Cache set: {key} (ttl={ttl})")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete cached value.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        redis = await self._get_redis()
        full_key = f"{self.prefix}{key}"

        try:
            result = await redis.delete(full_key)
            logger.debug(f"Cache delete: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "channel:*")

        Returns:
            Number of keys deleted
        """
        redis = await self._get_redis()
        full_pattern = f"{self.prefix}{pattern}"

        try:
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await redis.scan(
                    cursor,
                    match=full_pattern,
                    count=100
                )

                if keys:
                    deleted += await redis.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
            return deleted
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    async def clear_all(self) -> int:
        """
        Clear all YouTube cache entries.

        Returns:
            Number of keys deleted
        """
        return await self.clear_pattern("*")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
