"""
YouTube Data API v3 client with rate limiting and caching.
Handles all interactions with YouTube API.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import re
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httpx

from app.config import settings
from app.data_ingestion.rate_limiter import YouTubeRateLimiter
from app.data_ingestion.cache import YouTubeCache

logger = logging.getLogger(__name__)


class YouTubeAPIClient:
    """
    YouTube Data API v3 client.
    Provides methods to fetch channel and video data with rate limiting and caching.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limiter: Optional[YouTubeRateLimiter] = None,
        cache: Optional[YouTubeCache] = None,
    ):
        """
        Initialize YouTube API client.

        Args:
            api_key: YouTube API key (defaults to settings)
            rate_limiter: Custom rate limiter instance
            cache: Custom cache instance
        """
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YouTube API key is required")

        self.youtube = build("youtube", "v3", developerKey=self.api_key)
        self.rate_limiter = rate_limiter or YouTubeRateLimiter()
        self.cache = cache or YouTubeCache()

    async def get_channel_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by channel ID.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Channel data dict or None if not found
        """
        cache_key = f"channel:{channel_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for channel {channel_id}")
            return cached

        await self.rate_limiter.acquire(cost=1)  # channels.list costs 1 unit

        try:
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id,
            )
            response = await asyncio.to_thread(request.execute)

            if not response.get("items"):
                logger.warning(f"Channel {channel_id} not found")
                return None

            channel_data = response["items"][0]
            await self.cache.set(
                cache_key,
                channel_data,
                ttl=settings.CACHE_TTL_CHANNEL_DETAILS
            )

            return channel_data

        except HttpError as e:
            logger.error(f"Error fetching channel {channel_id}: {e}")
            raise

    async def get_channel_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by username/handle.

        Args:
            username: YouTube username or handle (without @)

        Returns:
            Channel data dict or None if not found
        """
        cache_key = f"channel:username:{username}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        await self.rate_limiter.acquire(cost=1)

        try:
            # Try with forUsername first
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                forUsername=username,
            )
            response = await asyncio.to_thread(request.execute)

            if response.get("items"):
                channel_data = response["items"][0]
                await self.cache.set(
                    cache_key,
                    channel_data,
                    ttl=settings.CACHE_TTL_CHANNEL_DETAILS
                )
                return channel_data

            # If not found, try searching
            return await self._search_channel_by_handle(username)

        except HttpError as e:
            logger.error(f"Error fetching channel by username {username}: {e}")
            raise

    async def _search_channel_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """Search for channel by handle using search API."""
        await self.rate_limiter.acquire(cost=100)  # search costs 100 units

        try:
            request = self.youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1,
            )
            response = await asyncio.to_thread(request.execute)

            if not response.get("items"):
                return None

            channel_id = response["items"][0]["snippet"]["channelId"]
            return await self.get_channel_by_id(channel_id)

        except HttpError as e:
            logger.error(f"Error searching for channel {handle}: {e}")
            return None

    async def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get videos from a channel's uploads playlist.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum results per page (1-50)
            page_token: Token for pagination

        Returns:
            Dict with 'items' (video IDs) and 'nextPageToken'
        """
        # First, get the uploads playlist ID
        channel_data = await self.get_channel_by_id(channel_id)
        if not channel_data:
            return {"items": [], "nextPageToken": None}

        uploads_playlist_id = (
            channel_data.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )

        if not uploads_playlist_id:
            logger.warning(f"No uploads playlist for channel {channel_id}")
            return {"items": [], "nextPageToken": None}

        await self.rate_limiter.acquire(cost=1)  # playlistItems.list costs 1 unit

        try:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(max_results, 50),
                pageToken=page_token,
            )
            response = await asyncio.to_thread(request.execute)

            video_ids = [
                item["contentDetails"]["videoId"]
                for item in response.get("items", [])
            ]

            return {
                "items": video_ids,
                "nextPageToken": response.get("nextPageToken"),
            }

        except HttpError as e:
            logger.error(f"Error fetching videos for channel {channel_id}: {e}")
            raise

    async def get_videos_details(
        self,
        video_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Get detailed information for multiple videos.
        Batches up to 50 videos per request.

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            List of video data dicts
        """
        if not video_ids:
            return []

        # Batch requests (max 50 IDs per request)
        batches = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
        all_videos = []

        for batch in batches:
            cache_key = f"videos:{'_'.join(sorted(batch))}"
            cached = await self.cache.get(cache_key)

            if cached:
                all_videos.extend(cached)
                continue

            await self.rate_limiter.acquire(cost=1)  # videos.list costs 1 unit

            try:
                request = self.youtube.videos().list(
                    part="snippet,contentDetails,statistics,status",
                    id=",".join(batch),
                )
                response = await asyncio.to_thread(request.execute)

                videos = response.get("items", [])
                await self.cache.set(
                    cache_key,
                    videos,
                    ttl=settings.CACHE_TTL_VIDEO_DETAILS
                )
                all_videos.extend(videos)

            except HttpError as e:
                logger.error(f"Error fetching video details: {e}")
                raise

        return all_videos

    async def get_video_statistics(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current statistics for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Statistics dict or None
        """
        cache_key = f"video:stats:{video_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        await self.rate_limiter.acquire(cost=1)

        try:
            request = self.youtube.videos().list(
                part="statistics",
                id=video_id,
            )
            response = await asyncio.to_thread(request.execute)

            if not response.get("items"):
                return None

            stats = response["items"][0].get("statistics", {})
            await self.cache.set(
                cache_key,
                stats,
                ttl=settings.CACHE_TTL_VIDEO_STATS
            )

            return stats

        except HttpError as e:
            logger.error(f"Error fetching statistics for video {video_id}: {e}")
            raise

    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100,
        page_token: Optional[str] = None,
        order: str = "relevance",  # relevance or time
    ) -> Dict[str, Any]:
        """
        Get comments for a video.

        Args:
            video_id: YouTube video ID
            max_results: Maximum results per page (1-100)
            page_token: Token for pagination
            order: Sort order ('relevance' or 'time')

        Returns:
            Dict with 'items' (comments) and 'nextPageToken'
        """
        await self.rate_limiter.acquire(cost=1)  # commentThreads.list costs 1 unit

        try:
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_results, 100),
                pageToken=page_token,
                order=order,
                textFormat="plainText",
            )
            response = await asyncio.to_thread(request.execute)

            comments = []
            for item in response.get("items", []):
                top_comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "id": item["id"],
                    "video_id": video_id,
                    "author_channel_id": top_comment.get("authorChannelId", {}).get("value"),
                    "text": top_comment.get("textOriginal", ""),
                    "like_count": top_comment.get("likeCount", 0),
                    "published_at": top_comment.get("publishedAt"),
                })

            return {
                "items": comments,
                "nextPageToken": response.get("nextPageToken"),
            }

        except HttpError as e:
            # Comments may be disabled
            if e.resp.status == 403:
                logger.info(f"Comments disabled for video {video_id}")
                return {"items": [], "nextPageToken": None}
            logger.error(f"Error fetching comments for video {video_id}: {e}")
            raise

    def parse_duration(self, duration: str) -> int:
        """
        Parse ISO 8601 duration to seconds.

        Args:
            duration: ISO 8601 duration string (e.g., "PT1H2M10S")

        Returns:
            Duration in seconds
        """
        match = re.match(
            r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',
            duration
        )
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    async def close(self) -> None:
        """Clean up resources."""
        await self.cache.close()
