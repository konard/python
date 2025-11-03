"""
API Key Manager for YouTube Data API v3

Manages multiple API keys with quota tracking, rotation, and fallback handling.
This ensures we can distribute requests across multiple keys and handle quota limits gracefully.
"""
import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app.core.config import settings


@dataclass
class APIKeyStatus:
    """Status information for a single API key"""
    key: str
    quota_used: int = 0
    quota_limit: int = 10000  # Default YouTube API quota
    last_reset: datetime = field(default_factory=datetime.now)
    is_disabled: bool = False
    disabled_until: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None


class APIKeyManager:
    """
    Manages multiple YouTube API keys with intelligent rotation and quota tracking.

    Features:
    - Automatic rotation across available keys
    - Quota tracking per key
    - Automatic disabling of exhausted keys
    - Daily quota reset (YouTube quotas reset at midnight Pacific Time)
    - Error tracking and temporary key disabling
    - Graceful fallback when keys are exhausted
    """

    def __init__(self, api_keys: Optional[List[str]] = None):
        """
        Initialize API key manager.

        Args:
            api_keys: List of YouTube API keys. If None, reads from settings.
        """
        if api_keys is None:
            api_keys = settings.youtube_api_keys_list

        if not api_keys:
            raise ValueError("At least one YouTube API key must be provided")

        self.keys: List[APIKeyStatus] = [
            APIKeyStatus(
                key=key,
                quota_limit=settings.youtube_api_quota_limit
            )
            for key in api_keys
        ]

        self._current_index = 0
        self._lock = asyncio.Lock()

    def _check_quota_reset(self, key_status: APIKeyStatus) -> None:
        """
        Check if quota should be reset (daily reset).
        YouTube quotas reset at midnight Pacific Time.
        """
        now = datetime.now()
        time_since_reset = now - key_status.last_reset

        # Reset if more than 24 hours have passed
        if time_since_reset > timedelta(hours=24):
            key_status.quota_used = 0
            key_status.last_reset = now
            key_status.error_count = 0
            # Re-enable if it was temporarily disabled due to quota
            if key_status.is_disabled and key_status.disabled_until:
                if now >= key_status.disabled_until:
                    key_status.is_disabled = False
                    key_status.disabled_until = None

    async def get_key_for_request(self, quota_cost: int = 1) -> Optional[str]:
        """
        Get an available API key for a request.

        Implements round-robin selection with quota checking.
        If a key is exhausted, it's skipped until quota resets.

        Args:
            quota_cost: Expected quota cost of the request (default: 1)

        Returns:
            API key string or None if all keys are exhausted

        Raises:
            ValueError: If all API keys have exceeded their quota limits
        """
        async with self._lock:
            attempts = 0
            max_attempts = len(self.keys)

            while attempts < max_attempts:
                # Get next key in rotation
                key_status = self.keys[self._current_index]

                # Check if quota should be reset
                self._check_quota_reset(key_status)

                # Move to next key for next request
                self._current_index = (self._current_index + 1) % len(self.keys)
                attempts += 1

                # Skip if disabled
                if key_status.is_disabled:
                    # Check if we should re-enable
                    if key_status.disabled_until and datetime.now() >= key_status.disabled_until:
                        key_status.is_disabled = False
                        key_status.disabled_until = None
                    else:
                        continue

                # Check if key has enough quota
                if key_status.quota_used + quota_cost <= key_status.quota_limit:
                    # Reserve the quota
                    key_status.quota_used += quota_cost
                    return key_status.key

            # All keys exhausted
            return None

    async def track_successful_request(self, api_key: str, quota_cost: int = 1) -> None:
        """
        Track a successful request (already counted in get_key_for_request).

        This method is kept for compatibility but quota is already tracked
        in get_key_for_request to ensure atomic reservation.

        Args:
            api_key: The API key that was used
            quota_cost: Quota cost of the request
        """
        # Quota already tracked in get_key_for_request
        pass

    async def track_failed_request(
        self,
        api_key: str,
        error_message: str,
        temporary_disable: bool = False,
        disable_duration_minutes: int = 60
    ) -> None:
        """
        Track a failed request and optionally disable the key temporarily.

        Args:
            api_key: The API key that failed
            error_message: Error message from the API
            temporary_disable: Whether to temporarily disable this key
            disable_duration_minutes: How long to disable the key (minutes)
        """
        async with self._lock:
            for key_status in self.keys:
                if key_status.key == api_key:
                    key_status.error_count += 1
                    key_status.last_error = error_message

                    if temporary_disable:
                        key_status.is_disabled = True
                        key_status.disabled_until = datetime.now() + timedelta(
                            minutes=disable_duration_minutes
                        )

                    # If quota exceeded error, disable until next reset
                    if "quota" in error_message.lower() or "exceeded" in error_message.lower():
                        key_status.is_disabled = True
                        # Disable for rest of the day (max 24 hours)
                        key_status.disabled_until = datetime.now() + timedelta(hours=24)

                    break

    def get_quota_status(self) -> Dict[str, Dict[str, any]]:
        """
        Get quota status for all keys.

        Returns:
            Dictionary with quota information for each key
        """
        status = {}
        for i, key_status in enumerate(self.keys):
            self._check_quota_reset(key_status)

            # Mask the key for security (show only last 4 chars)
            masked_key = f"***{key_status.key[-4:]}" if len(key_status.key) > 4 else "***"

            status[f"key_{i+1}"] = {
                "key": masked_key,
                "quota_used": key_status.quota_used,
                "quota_limit": key_status.quota_limit,
                "quota_remaining": key_status.quota_limit - key_status.quota_used,
                "usage_percent": round(
                    (key_status.quota_used / key_status.quota_limit) * 100, 2
                ),
                "is_disabled": key_status.is_disabled,
                "disabled_until": key_status.disabled_until.isoformat()
                if key_status.disabled_until
                else None,
                "error_count": key_status.error_count,
                "last_error": key_status.last_error,
                "last_reset": key_status.last_reset.isoformat(),
            }

        return status

    def get_total_quota_available(self) -> int:
        """
        Get total remaining quota across all active keys.

        Returns:
            Total quota units remaining
        """
        total = 0
        for key_status in self.keys:
            self._check_quota_reset(key_status)
            if not key_status.is_disabled:
                total += key_status.quota_limit - key_status.quota_used
        return total

    def has_available_quota(self, required_quota: int = 1) -> bool:
        """
        Check if there's enough quota available across all keys.

        Args:
            required_quota: Required quota units

        Returns:
            True if enough quota is available
        """
        return self.get_total_quota_available() >= required_quota


# Global instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance (singleton)"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
