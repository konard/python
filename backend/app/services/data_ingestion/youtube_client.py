"""YouTube Data API v3 client with rate limiting and caching"""
import re
import isodate
import redis.asyncio as redis
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings


class YouTubeAPIClient:
    """
    YouTube Data API v3 client with:
    - Rate limiting to respect quota
    - Redis caching to minimize API calls
    - Batch requests for efficiency
    """

    def __init__(self):
        self.api_key = settings.youtube_api_key
        self.youtube = build("youtube", "v3", developerKey=self.api_key)
        self.redis_client: Optional[redis.Redis] = None
        self._quota_used = 0
        self._quota_limit = settings.youtube_api_quota_limit

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

    def _track_quota(self, units: int) -> None:
        """Track API quota usage"""
        self._quota_used += units
        if self._quota_used > self._quota_limit:
            print(f"Warning: Quota limit reached ({self._quota_used}/{self._quota_limit})")

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

        try:
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )
            response = await asyncio.to_thread(request.execute)
            self._track_quota(1)

            if not response.get("items"):
                return None

            channel_data = response["items"][0]
            await self._cache_set(cache_key, channel_data, settings.cache_ttl_channel)
            return channel_data

        except HttpError as e:
            print(f"YouTube API error: {e}")
            return None

    async def get_channel_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by username/handle.

        Args:
            username: YouTube username or handle (without @)

        Returns:
            Channel data dict or None if not found

        Quota cost: 1 unit
        """
        cache_key = f"youtube:channel:username:{username}"
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        try:
            # Try forUsername first
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                forUsername=username
            )
            response = await asyncio.to_thread(request.execute)
            self._track_quota(1)

            if response.get("items"):
                channel_data = response["items"][0]
                await self._cache_set(cache_key, channel_data, settings.cache_ttl_channel)
                return channel_data

            # If not found, try forHandle (for @handle format)
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                forHandle=username
            )
            response = await asyncio.to_thread(request.execute)
            self._track_quota(1)

            if response.get("items"):
                channel_data = response["items"][0]
                await self._cache_set(cache_key, channel_data, settings.cache_ttl_channel)
                return channel_data

            return None

        except HttpError as e:
            print(f"YouTube API error: {e}")
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

        try:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(max_results, 50),
                pageToken=page_token
            )
            response = await asyncio.to_thread(request.execute)
            self._track_quota(1)

            video_ids = [
                item["contentDetails"]["videoId"]
                for item in response.get("items", [])
            ]

            return {
                "items": video_ids,
                "nextPageToken": response.get("nextPageToken")
            }

        except HttpError as e:
            print(f"YouTube API error: {e}")
            return {"items": [], "nextPageToken": None}

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

            try:
                request = self.youtube.videos().list(
                    part="snippet,contentDetails,statistics,status",
                    id=batch_str
                )
                response = await asyncio.to_thread(request.execute)
                self._track_quota(1)

                videos = response.get("items", [])
                all_videos.extend(videos)

                await self._cache_set(cache_key, videos, settings.cache_ttl_video)

            except HttpError as e:
                print(f"YouTube API error: {e}")

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
        try:
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_results, 100),
                order=order,
                pageToken=page_token,
                textFormat="plainText"
            )
            response = await asyncio.to_thread(request.execute)
            self._track_quota(1)

            return {
                "items": response.get("items", []),
                "nextPageToken": response.get("nextPageToken")
            }

        except HttpError as e:
            # Comments might be disabled
            print(f"YouTube API error getting comments: {e}")
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
