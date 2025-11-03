"""
API Key Manager for YouTube Data API v3

Manages multiple API keys with:
- Quota tracking per key
- Automatic rotation when quota is reached
- Retry logic and backoff
- Key health monitoring
"""
import asyncio
import redis.asyncio as redis
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from enum import Enum

from app.core.config import settings


class KeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class APIKeyInfo:
    """Information about an API key"""
    key: str
    status: KeyStatus
    quota_used: int
    quota_limit: int
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    disabled_until: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        """Check if key is available for use"""
        if self.status == KeyStatus.DISABLED:
            if self.disabled_until and datetime.utcnow() < self.disabled_until:
                return False
            # Re-enable if cooldown period passed
            self.status = KeyStatus.ACTIVE
            self.disabled_until = None

        return (
            self.status == KeyStatus.ACTIVE and
            self.quota_used < self.quota_limit
        )

    @property
    def quota_remaining(self) -> int:
        """Get remaining quota"""
        return max(0, self.quota_limit - self.quota_used)

    @property
    def quota_percentage(self) -> float:
        """Get quota usage percentage"""
        if self.quota_limit == 0:
            return 100.0
        return (self.quota_used / self.quota_limit) * 100


class APIKeyManager:
    """
    Manages multiple YouTube API keys with quota tracking and rotation.

    Features:
    - Stores multiple API keys
    - Tracks quota usage per key (stored in Redis with daily reset)
    - Automatically rotates to next available key when quota reached
    - Handles rate limit errors with backoff
    - Monitors key health
    """

    def __init__(self, api_keys: List[str], quota_limit_per_key: int = 10000):
        """
        Initialize API key manager.

        Args:
            api_keys: List of YouTube Data API v3 keys
            quota_limit_per_key: Daily quota limit per key (default: 10,000)
        """
        if not api_keys:
            raise ValueError("At least one API key must be provided")

        self.api_keys = api_keys
        self.quota_limit = quota_limit_per_key
        self.redis_client: Optional[redis.Redis] = None
        self._current_key_index = 0
        self._key_infos: Dict[str, APIKeyInfo] = {}

        # Initialize key info
        for key in api_keys:
            self._key_infos[key] = APIKeyInfo(
                key=key,
                status=KeyStatus.ACTIVE,
                quota_used=0,
                quota_limit=quota_limit_per_key
            )

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    def _get_redis_key(self, api_key: str) -> str:
        """Get Redis key for storing quota info"""
        # Hash the key for privacy (store only last 8 chars)
        key_suffix = api_key[-8:] if len(api_key) > 8 else api_key
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"youtube:quota:{key_suffix}:{today}"

    async def _load_quota_from_redis(self, api_key: str) -> int:
        """Load quota usage from Redis"""
        try:
            r = await self._get_redis()
            redis_key = self._get_redis_key(api_key)
            value = await r.get(redis_key)
            if value:
                return int(value)
        except Exception as e:
            print(f"Error loading quota from Redis: {e}")
        return 0

    async def _save_quota_to_redis(self, api_key: str, quota_used: int) -> None:
        """Save quota usage to Redis with 24h expiry"""
        try:
            r = await self._get_redis()
            redis_key = self._get_redis_key(api_key)
            # Set with expiry at end of day (UTC)
            now = datetime.utcnow()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            ttl = int((tomorrow - now).total_seconds())
            await r.setex(redis_key, ttl, str(quota_used))
        except Exception as e:
            print(f"Error saving quota to Redis: {e}")

    async def initialize(self) -> None:
        """Initialize manager by loading quota from Redis"""
        for api_key in self.api_keys:
            quota_used = await self._load_quota_from_redis(api_key)
            self._key_infos[api_key].quota_used = quota_used

    async def get_key_for_request(self) -> str:
        """
        Get an available API key for making a request.

        Uses round-robin selection among available keys.

        Returns:
            API key string

        Raises:
            RuntimeError: If no keys are available
        """
        # Load current quota for all keys
        for api_key in self.api_keys:
            quota_used = await self._load_quota_from_redis(api_key)
            self._key_infos[api_key].quota_used = quota_used

        # Try to find an available key, starting from current index
        attempts = 0
        while attempts < len(self.api_keys):
            key = self.api_keys[self._current_key_index]
            key_info = self._key_infos[key]

            if key_info.is_available:
                # Move to next key for next request (round-robin)
                self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
                return key

            # Try next key
            self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
            attempts += 1

        # No keys available
        raise RuntimeError(
            "No API keys available. All keys have reached quota limit or are disabled. "
            f"Status: {self.get_all_keys_status()}"
        )

    async def track_request(self, api_key: str, quota_cost: int) -> None:
        """
        Track a successful API request.

        Args:
            api_key: The API key that was used
            quota_cost: Quota units consumed by the request
        """
        if api_key not in self._key_infos:
            return

        key_info = self._key_infos[api_key]
        key_info.quota_used += quota_cost

        # Check if quota exceeded
        if key_info.quota_used >= key_info.quota_limit:
            key_info.status = KeyStatus.QUOTA_EXCEEDED
            print(f"API key {api_key[-8:]} has reached quota limit ({key_info.quota_used}/{key_info.quota_limit})")

        # Save to Redis
        await self._save_quota_to_redis(api_key, key_info.quota_used)

    async def handle_error(
        self,
        api_key: str,
        error: Exception,
        disable_duration_minutes: int = 60
    ) -> None:
        """
        Handle an error from YouTube API.

        Args:
            api_key: The API key that encountered the error
            error: The exception that occurred
            disable_duration_minutes: How long to disable the key (default: 60 min)
        """
        if api_key not in self._key_infos:
            return

        key_info = self._key_infos[api_key]
        error_msg = str(error)

        # Check if it's a quota error
        if "quota" in error_msg.lower() or "quotaExceeded" in error_msg:
            key_info.status = KeyStatus.QUOTA_EXCEEDED
            key_info.quota_used = key_info.quota_limit
            await self._save_quota_to_redis(api_key, key_info.quota_used)
            print(f"API key {api_key[-8:]} quota exceeded: {error_msg}")

        # Check if it's a rate limit error (429)
        elif "429" in error_msg or "rate" in error_msg.lower():
            key_info.status = KeyStatus.DISABLED
            key_info.disabled_until = datetime.utcnow() + timedelta(minutes=disable_duration_minutes)
            print(f"API key {api_key[-8:]} rate limited, disabled for {disable_duration_minutes} minutes")

        # Other errors
        else:
            key_info.status = KeyStatus.ERROR
            key_info.last_error = error_msg
            key_info.last_error_time = datetime.utcnow()
            print(f"API key {api_key[-8:]} error: {error_msg}")

    def get_key_status(self, api_key: str) -> Optional[Dict]:
        """Get status information for a specific key"""
        if api_key not in self._key_infos:
            return None

        key_info = self._key_infos[api_key]
        return {
            "key_suffix": api_key[-8:],
            "status": key_info.status.value,
            "quota_used": key_info.quota_used,
            "quota_limit": key_info.quota_limit,
            "quota_remaining": key_info.quota_remaining,
            "quota_percentage": round(key_info.quota_percentage, 2),
            "is_available": key_info.is_available,
            "last_error": key_info.last_error,
            "last_error_time": key_info.last_error_time.isoformat() if key_info.last_error_time else None,
            "disabled_until": key_info.disabled_until.isoformat() if key_info.disabled_until else None,
        }

    def get_all_keys_status(self) -> List[Dict]:
        """Get status information for all keys"""
        return [
            self.get_key_status(key)
            for key in self.api_keys
        ]

    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()


# Singleton instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get singleton API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        # Parse API keys from settings (comma-separated)
        api_keys_str = settings.youtube_api_keys
        api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]

        _api_key_manager = APIKeyManager(
            api_keys=api_keys,
            quota_limit_per_key=settings.youtube_api_quota_limit
        )
    return _api_key_manager
