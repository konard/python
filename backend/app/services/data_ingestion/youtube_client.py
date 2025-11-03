"""YouTube Data API v3 client with multi-key support and caching"""
import re
import isodate
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
from cachetools import TTLCache

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.services.api_key_manager import get_api_key_manager


class YouTubeAPIClient:
    """
    YouTube Data API v3 client with:
    - Multi-key support with intelligent rotation
    - Quota tracking per key
    - In-memory caching to minimize API calls
    - Batch requests for efficiency
    """

    def __init__(self):
        self.api_key_manager = get_api_key_manager()
        # In-memory cache with TTL (size: 1000 items, TTL: varies by cache)
        self._cache: Dict[str, TTLCache] = {
            'channel': TTLCache(maxsize=500, ttl=settings.cache_ttl_channel),
            'video': TTLCache(maxsize=500, ttl=settings.cache_ttl_video),
        }

    def _get_youtube_client(self, api_key: str):
        """Build YouTube API client with specific key"""
        return build("youtube", "v3", developerKey=api_key, cache_discovery=False)

    async def _cache_get(self, cache_type: str, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        try:
            return self._cache[cache_type].get(key)
        except Exception:
            return None

    def _cache_set(self, cache_type: str, key: str, value: Dict[str, Any]) -> None:
        """Set value in cache (TTL handled by TTLCache)"""
        try:
            self._cache[cache_type][key] = value
        except Exception:
            pass

    async def _make_api_call(
        self,
        api_call_func,
        quota_cost: int = 1,
        cache_type: Optional[str] = None,
        cache_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make API call with key rotation and error handling.

        Args:
            api_call_func: Function that takes youtube client and returns request object
            quota_cost: Quota cost of this call
            cache_type: Type of cache to use
            cache_key: Cache key for this call

        Returns:
            API response or None if failed
        """
        # Check cache first
        if cache_type and cache_key:
            cached = await self._cache_get(cache_type, cache_key)
            if cached:
                return cached

        # Get API key from manager
        api_key = await self.api_key_manager.get_key_for_request(quota_cost)
        if not api_key:
            print("ERROR: All API keys have exceeded their quota limits!")
            return None

        try:
            # Build client with selected key
            youtube = self._get_youtube_client(api_key)

            # Make API call
            request = api_call_func(youtube)
            response = await asyncio.to_thread(request.execute)

            # Cache the response
            if cache_type and cache_key:
                self._cache_set(cache_type, cache_key, response)

            return response

        except HttpError as e:
            error_msg = str(e)
            print(f"YouTube API error: {error_msg}")

            # Track failed request
            await self.api_key_manager.track_failed_request(
                api_key=api_key,
                error_message=error_msg,
                temporary_disable="quota" in error_msg.lower() or "exceeded" in error_msg.lower()
            )

            return None

    async def get_channel_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by channel ID.

        Args:
            channel_id: YouTube channel ID (e.g., "UCxxxxxxxx")

        Returns:
            Channel data dict or None if not found

        Quota cost: 1 unit
        """
        def api_call(youtube):
            return youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )

        response = await self._make_api_call(
            api_call_func=api_call,
            quota_cost=1,
            cache_type='channel',
            cache_key=f"channel:{channel_id}"
        )

        if response and response.get("items"):
            return response["items"][0]

        return None

    async def get_channel_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by username/handle.

        Args:
            username: YouTube username or handle (without @)

        Returns:
            Channel data dict or None if not found

        Quota cost: 1-2 units (tries forUsername, then forHandle)
        """
        # Try forUsername first
        def api_call_username(youtube):
            return youtube.channels().list(
                part="snippet,statistics,contentDetails",
                forUsername=username
            )

        response = await self._make_api_call(
            api_call_func=api_call_username,
            quota_cost=1,
            cache_type='channel',
            cache_key=f"channel:username:{username}"
        )

        if response and response.get("items"):
            return response["items"][0]

        # If not found, try forHandle (for @handle format)
        def api_call_handle(youtube):
            return youtube.channels().list(
                part="snippet,statistics,contentDetails",
                forHandle=username
            )

        response = await self._make_api_call(
            api_call_func=api_call_handle,
            quota_cost=1,
            cache_type='channel',
            cache_key=f"channel:handle:{username}"
        )

        if response and response.get("items"):
            return response["items"][0]

        return None

    async def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get videos from a channel's uploads playlist.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum results per page (max 50)
            page_token: Page token for pagination

        Returns:
            Dict with 'items' (video IDs) and 'nextPageToken'

        Quota cost: 1 unit per request
        """
        # First, get the uploads playlist ID
        channel_data = await self.get_channel_by_id(channel_id)
        if not channel_data:
            return {"items": [], "nextPageToken": None}

        uploads_playlist_id = channel_data["contentDetails"]["relatedPlaylists"]["uploads"]

        def api_call(youtube):
            return youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(max_results, 50),
                pageToken=page_token
            )

        response = await self._make_api_call(
            api_call_func=api_call,
            quota_cost=1
        )

        if not response:
            return {"items": [], "nextPageToken": None}

        video_ids = [
            item["contentDetails"]["videoId"]
            for item in response.get("items", [])
        ]

        return {
            "items": video_ids,
            "nextPageToken": response.get("nextPageToken")
        }

    async def get_videos_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed information for multiple videos.

        Args:
            video_ids: List of video IDs (max 50 per batch)

        Returns:
            List of video data dicts

        Quota cost: 1 unit per request (batched up to 50 videos)
        """
        if not video_ids:
            return []

        # Batch requests in chunks of 50
        all_videos = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            batch_str = ",".join(batch)

            def api_call(youtube):
                return youtube.videos().list(
                    part="snippet,contentDetails,statistics,status",
                    id=batch_str
                )

            response = await self._make_api_call(
                api_call_func=api_call,
                quota_cost=1,
                cache_type='video',
                cache_key=f"videos:{batch_str}"
            )

            if response:
                all_videos.extend(response.get("items", []))

        return all_videos

    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100,
        order: str = "relevance",
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comments for a video.

        Args:
            video_id: YouTube video ID
            max_results: Maximum results per page (max 100)
            order: Sort order ('time' or 'relevance')
            page_token: Page token for pagination

        Returns:
            Dict with 'items' (comments) and 'nextPageToken'

        Quota cost: 1 unit per request
        """
        def api_call(youtube):
            return youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_results, 100),
                order=order,
                pageToken=page_token,
                textFormat="plainText"
            )

        response = await self._make_api_call(
            api_call_func=api_call,
            quota_cost=1
        )

        if response:
            return {
                "items": response.get("items", []),
                "nextPageToken": response.get("nextPageToken")
            }

        # Comments might be disabled
        return {"items": [], "nextPageToken": None}

    @staticmethod
    def parse_duration(duration_str: str) -> int:
        """
        Parse ISO 8601 duration to seconds.

        Args:
            duration_str: ISO 8601 duration (e.g., "PT1H23M45S")

        Returns:
            Duration in seconds
        """
        try:
            duration = isodate.parse_duration(duration_str)
            return int(duration.total_seconds())
        except Exception:
            return 0

    def get_quota_status(self) -> Dict[str, Any]:
        """Get quota status from API key manager"""
        return self.api_key_manager.get_quota_status()


# Singleton instance
_youtube_client: Optional[YouTubeAPIClient] = None


def get_youtube_client() -> YouTubeAPIClient:
    """Get singleton YouTube API client instance"""
    global _youtube_client
    if _youtube_client is None:
        _youtube_client = YouTubeAPIClient()
    return _youtube_client
