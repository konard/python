"""Service for ingesting and managing YouTube video data"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoStatsSnapshot
from app.models.channel import Channel
from app.services.data_ingestion.youtube_client import get_youtube_client


class VideoIngestionService:
    """Service for ingesting YouTube video data"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.youtube = get_youtube_client()

    async def import_channel_videos(
        self,
        channel_id: int,
        max_videos: Optional[int] = None
    ) -> List[Video]:
        """
        Import all videos from a channel.

        Args:
            channel_id: Internal channel ID
            max_videos: Maximum number of videos to import (None = all)

        Returns:
            List of imported Video models
        """
        # Get channel
        stmt = select(Channel).where(Channel.id == channel_id)
        result = await self.db.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            return []

        imported_videos = []
        page_token = None
        total_fetched = 0

        # Fetch videos in batches
        while True:
            # Get video IDs from channel
            response = await self.youtube.get_channel_videos(
                channel.youtube_channel_id,
                max_results=50,
                page_token=page_token
            )

            video_ids = response["items"]
            if not video_ids:
                break

            # Get video details
            videos_data = await self.youtube.get_videos_details(video_ids)

            # Process each video
            for video_data in videos_data:
                video = await self._process_video_data(video_data, channel_id)
                if video:
                    imported_videos.append(video)

            total_fetched += len(video_ids)

            # Check if we've reached the limit
            if max_videos and total_fetched >= max_videos:
                break

            # Get next page
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return imported_videos

    async def _process_video_data(
        self,
        video_data: dict,
        channel_id: int
    ) -> Optional[Video]:
        """
        Process and save video data from YouTube API.

        Args:
            video_data: Video data from YouTube API
            channel_id: Internal channel ID

        Returns:
            Created or updated Video model
        """
        youtube_video_id = video_data["id"]
        snippet = video_data["snippet"]
        content_details = video_data.get("contentDetails", {})
        statistics = video_data.get("statistics", {})
        status = video_data.get("status", {})

        # Check if video already exists
        stmt = select(Video).where(Video.youtube_video_id == youtube_video_id)
        result = await self.db.execute(stmt)
        existing_video = result.scalar_one_or_none()

        # Parse duration
        duration_seconds = self.youtube.parse_duration(
            content_details.get("duration", "PT0S")
        )

        if existing_video:
            # Update existing video
            existing_video.title = snippet.get("title", "")
            existing_video.description = snippet.get("description")
            existing_video.tags = snippet.get("tags", [])
            existing_video.category_id = snippet.get("categoryId")
            existing_video.duration_seconds = duration_seconds
            existing_video.status = status.get("privacyStatus")
            existing_video.thumbnails = snippet.get("thumbnails", {})
            existing_video.definition = content_details.get("definition")
            existing_video.dimension = content_details.get("dimension")
            existing_video.updated_at = datetime.utcnow()

            self.db.add(existing_video)
            await self.db.commit()
            await self.db.refresh(existing_video)

            # Create stats snapshot
            await self.create_stats_snapshot(existing_video.id, statistics)

            return existing_video

        # Create new video
        video = Video(
            youtube_video_id=youtube_video_id,
            channel_id=channel_id,
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            tags=snippet.get("tags", []),
            category_id=snippet.get("categoryId"),
            duration_seconds=duration_seconds,
            published_at=datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            ),
            status=status.get("privacyStatus"),
            thumbnails=snippet.get("thumbnails", {}),
            definition=content_details.get("definition"),
            dimension=content_details.get("dimension"),
        )

        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)

        # Create initial stats snapshot
        await self.create_stats_snapshot(video.id, statistics, source="import")

        return video

    async def create_stats_snapshot(
        self,
        video_id: int,
        statistics: dict,
        source: str = "manual"
    ) -> VideoStatsSnapshot:
        """
        Create a statistics snapshot for a video.

        Args:
            video_id: Internal video ID
            statistics: Statistics dict from YouTube API
            source: Source of snapshot (manual, import, daily_cron, etc.)

        Returns:
            Created VideoStatsSnapshot
        """
        snapshot = VideoStatsSnapshot(
            video_id=video_id,
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            favorite_count=int(statistics.get("favoriteCount", 0)),
            source=source,
        )

        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def update_video_stats(self, video_id: int) -> Optional[VideoStatsSnapshot]:
        """
        Update statistics for an existing video.

        Args:
            video_id: Internal video ID

        Returns:
            Created VideoStatsSnapshot or None if video not found
        """
        # Get video
        stmt = select(Video).where(Video.id == video_id)
        result = await self.db.execute(stmt)
        video = result.scalar_one_or_none()

        if not video:
            return None

        # Fetch latest data from YouTube
        videos_data = await self.youtube.get_videos_details([video.youtube_video_id])
        if not videos_data:
            return None

        video_data = videos_data[0]
        statistics = video_data.get("statistics", {})

        return await self.create_stats_snapshot(
            video_id,
            statistics,
            source="daily_cron"
        )

    async def get_channel_videos(
        self,
        channel_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Video]:
        """
        Get videos for a channel from database.

        Args:
            channel_id: Internal channel ID
            limit: Maximum number of videos to return
            offset: Number of videos to skip

        Returns:
            List of Video models
        """
        stmt = (
            select(Video)
            .where(Video.channel_id == channel_id)
            .order_by(Video.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
