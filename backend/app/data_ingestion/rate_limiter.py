"""
Rate limiter for YouTube Data API v3.
Tracks quota usage and enforces limits.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class YouTubeRateLimiter:
    """
    Rate limiter for YouTube Data API.
    Uses Redis to track quota usage across multiple workers.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL (defaults to settings)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[aioredis.Redis] = None
        self.quota_limit = settings.YOUTUBE_API_QUOTA_LIMIT
        self.requests_per_second = settings.YOUTUBE_API_REQUESTS_PER_SECOND

        # Keys for Redis
        self.quota_key = "youtube:api:quota"
        self.rate_key = "youtube:api:rate"

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self.redis

    async def acquire(self, cost: int = 1) -> None:
        """
        Acquire quota units before making an API request.
        Blocks if quota is exhausted.

        Args:
            cost: Number of quota units (default 1)
        """
        redis = await self._get_redis()

        # Check and enforce daily quota
        await self._check_daily_quota(redis, cost)

        # Enforce rate limiting (requests per second)
        await self._check_rate_limit(redis)

        # Increment quota usage
        await self._increment_quota(redis, cost)

    async def _check_daily_quota(self, redis: aioredis.Redis, cost: int) -> None:
        """Check if we have enough daily quota remaining."""
        current_usage = await redis.get(self.quota_key)
        current_usage = int(current_usage) if current_usage else 0

        if current_usage + cost > self.quota_limit:
            # Calculate time until quota reset
            reset_time = self._get_quota_reset_time()
            wait_seconds = (reset_time - datetime.now()).total_seconds()

            if wait_seconds > 0:
                logger.warning(
                    f"Daily quota exhausted ({current_usage}/{self.quota_limit}). "
                    f"Waiting {wait_seconds:.0f} seconds until reset."
                )
                await asyncio.sleep(wait_seconds)
            else:
                # Reset quota if past reset time
                await redis.delete(self.quota_key)

    async def _check_rate_limit(self, redis: aioredis.Redis) -> None:
        """Enforce requests per second limit."""
        current_count = await redis.get(self.rate_key)
        current_count = int(current_count) if current_count else 0

        if current_count >= self.requests_per_second:
            # Wait until next second
            await asyncio.sleep(1.0)
            current_count = 0

        # Increment rate counter with 1-second expiry
        pipe = redis.pipeline()
        pipe.incr(self.rate_key)
        pipe.expire(self.rate_key, 1)
        await pipe.execute()

    async def _increment_quota(self, redis: aioredis.Redis, cost: int) -> None:
        """Increment the daily quota usage."""
        reset_time = self._get_quota_reset_time()
        ttl = int((reset_time - datetime.now()).total_seconds())

        pipe = redis.pipeline()
        pipe.incrby(self.quota_key, cost)
        pipe.expire(self.quota_key, ttl)
        await pipe.execute()

        new_usage = await redis.get(self.quota_key)
        logger.debug(f"Quota usage: {new_usage}/{self.quota_limit}")

    def _get_quota_reset_time(self) -> datetime:
        """
        Calculate the next quota reset time.
        YouTube quota resets at midnight Pacific Time.
        """
        now = datetime.now()
        reset_hour = settings.YOUTUBE_API_QUOTA_RESET_HOUR

        # Calculate next reset time
        today_reset = now.replace(
            hour=reset_hour,
            minute=0,
            second=0,
            microsecond=0
        )

        if now >= today_reset:
            # Reset is tomorrow
            return today_reset + timedelta(days=1)
        else:
            # Reset is today
            return today_reset

    async def get_remaining_quota(self) -> int:
        """Get remaining daily quota."""
        redis = await self._get_redis()
        current_usage = await redis.get(self.quota_key)
        current_usage = int(current_usage) if current_usage else 0
        return max(0, self.quota_limit - current_usage)

    async def reset_quota(self) -> None:
        """Manually reset quota (for testing/admin purposes)."""
        redis = await self._get_redis()
        await redis.delete(self.quota_key)
        logger.info("Quota manually reset")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
