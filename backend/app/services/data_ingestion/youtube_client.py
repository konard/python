"""YouTube Data API v3 client with rate limiting and caching"""
import asyncio
import json

import isodate
import redis.asyncio as redis
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.data_ingestion.api_key_manager import get_api_key_manager


class YouTubeAPIClient:
    """
    YouTube Data API v3 client with:
    - Multiple API key support with automatic rotation
    - Rate limiting to respect quota per key
    - Redis caching to minimize API calls
    - Batch requests for efficiency
    """

    def __init__(self):
        self.api_key_manager = get_api_key_manager()
        self.redis_client: Optional[redis.Redis] = None
        self._youtube_services: Dict[str, Any] = {}  # Cache youtube service per key

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        try:
            r = await self._get_redis()
            value = await r.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            # Log but don't fail on cache errors
            print(f"Cache get error: {e}")
        return None

    async def _cache_set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        """Set value in cache with TTL"""
        try:
            r = await self._get_redis()
            await r.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            # Log but don't fail on cache errors
            print(f"Cache set error: {e}")

    def _get_youtube_service(self, api_key: str) -> Any:
        """Get or create YouTube service for a specific API key"""
        if api_key not in self._youtube_services:
            self._youtube_services[api_key] = build("youtube", "v3", developerKey=api_key)
        return self._youtube_services[api_key]

    async def _execute_with_key_rotation(self, request_builder, quota_cost: int = 1) -> Optional[Dict[str, Any]]:
        """
        Execute a YouTube API request with automatic key rotation on failure.

        Args:
            request_builder: Function that takes api_key and returns a YouTube API request
            quota_cost: Quota units consumed by this request

        Returns:
            API response dict or None on failure
        """
        # Try up to 3 times with different keys
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get an available API key
                api_key = await self.api_key_manager.get_key_for_request()

                # Build and execute request
                youtube_service = self._get_youtube_service(api_key)
                request = request_builder(youtube_service)
                response = await asyncio.to_thread(request.execute)

                # Track successful request
                await self.api_key_manager.track_request(api_key, quota_cost)

                return response

            except HttpError as e:
                # Handle error and mark key if needed
                error_msg = str(e)
                if attempt < max_retries - 1:
                    # Try to get another key
                    await self.api_key_manager.handle_error(api_key, e)
                    print(f"YouTube API error (attempt {attempt + 1}/{max_retries}): {error_msg}. Trying another key...")
                    continue
                else:
                    # Last attempt failed
                    await self.api_key_manager.handle_error(api_key, e)
                    print(f"YouTube API error (all attempts failed): {error_msg}")
                    return None
            except Exception as e:
                print(f"Unexpected error in YouTube API call: {e}")
                return None

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
        cache_key = f"youtube:channel:{channel_id}"
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        def request_builder(youtube_service):
            return youtube_service.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )

        response = await self._execute_with_key_rotation(request_builder, quota_cost=1)

        if not response or not response.get("items"):
            return None

        channel_data = response["items"][0]
        await self._cache_set(cache_key, channel_data, settings.cache_ttl_channel)
        return channel_data

    async def get_channel_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by username/handle.

        Args:
            username: YouTube username or handle (without @)

        Returns:
            Channel data dict or None if not found

        Quota cost: 1-2 units
        """
        cache_key = f"youtube:channel:username:{username}"
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        # Try forUsername first
        def request_builder_username(youtube_service):
            return youtube_service.channels().list(
                part="snippet,statistics,contentDetails",
                forUsername=username
            )

        response = await self._execute_with_key_rotation(request_builder_username, quota_cost=1)

        if response and response.get("items"):
            channel_data = response["items"][0]
            await self._cache_set(cache_key, channel_data, settings.cache_ttl_channel)
            return channel_data

        # If not found, try forHandle (for @handle format)
        def request_builder_handle(youtube_service):
            return youtube_service.channels().list(
                part="snippet,statistics,contentDetails",
                forHandle=username
            )

        response = await self._execute_with_key_rotation(request_builder_handle, quota_cost=1)

        if response and response.get("items"):
            channel_data = response["items"][0]
            await self._cache_set(cache_key, channel_data, settings.cache_ttl_channel)
            return channel_data

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

        def request_builder(youtube_service):
            return youtube_service.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(max_results, 50),
                pageToken=page_token
            )

        response = await self._execute_with_key_rotation(request_builder, quota_cost=1)

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

            # Check cache first
            cache_key = f"youtube:videos:{batch_str}"
            cached = await self._cache_get(cache_key)
            if cached:
                all_videos.extend(cached)
                continue

            def request_builder(youtube_service, video_ids=batch_str):
                return youtube_service.videos().list(
                    part="snippet,contentDetails,statistics,status",
                    id=video_ids
                )

            response = await self._execute_with_key_rotation(request_builder, quota_cost=1)

            if response:
                videos = response.get("items", [])
                all_videos.extend(videos)
                await self._cache_set(cache_key, videos, settings.cache_ttl_video)

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
        def request_builder(youtube_service):
            return youtube_service.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_results, 100),
                order=order,
                pageToken=page_token,
                textFormat="plainText"
            )

        response = await self._execute_with_key_rotation(request_builder, quota_cost=1)

        if not response:
            # Comments might be disabled or error occurred
            return {"items": [], "nextPageToken": None}

        return {
            "items": response.get("items", []),
            "nextPageToken": response.get("nextPageToken")
        }

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

    async def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()


# Singleton instance
_youtube_client: Optional[YouTubeAPIClient] = None


def get_youtube_client() -> YouTubeAPIClient:
    """Get singleton YouTube API client instance"""
    global _youtube_client
    if _youtube_client is None:
        _youtube_client = YouTubeAPIClient()
    return _youtube_client
