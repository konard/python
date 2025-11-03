"""Service for ingesting and managing YouTube channel data"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel, ChannelStatsSnapshot
from app.services.data_ingestion.youtube_client import get_youtube_client
from app.utils.youtube_url_parser import parse_youtube_url


class ChannelIngestionService:
    """Service for ingesting YouTube channel data"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.youtube = get_youtube_client()

    async def add_channel_by_url(self, url: str, is_own: bool = False) -> Optional[Channel]:
        """
        Add a channel by URL or handle.

        Args:
            url: YouTube channel URL, handle, or video URL
            is_own: Whether this is user's own channel

        Returns:
            Channel model if successfully added, None otherwise
        """
        # Parse URL to extract identifiers
        channel_id, username, video_id = parse_youtube_url(url)

        # Get channel data from YouTube API
        channel_data = None

        if channel_id:
            channel_data = await self.youtube.get_channel_by_id(channel_id)
        elif username:
            channel_data = await self.youtube.get_channel_by_username(username)
        elif video_id:
            # Get video details to extract channel ID
            videos = await self.youtube.get_videos_details([video_id])
            if videos:
                video_channel_id = videos[0]["snippet"]["channelId"]
                channel_data = await self.youtube.get_channel_by_id(video_channel_id)

        if not channel_data:
            return None

        # Extract channel info
        youtube_channel_id = channel_data["id"]
        snippet = channel_data["snippet"]
        statistics = channel_data.get("statistics", {})

        # Check if channel already exists
        stmt = select(Channel).where(Channel.youtube_channel_id == youtube_channel_id)
        result = await self.db.execute(stmt)
        existing_channel = result.scalar_one_or_none()

        if existing_channel:
            # Update existing channel
            existing_channel.title = snippet.get("title", "")
            existing_channel.description = snippet.get("description")
            existing_channel.custom_url = snippet.get("customUrl")
            existing_channel.country = snippet.get("country")
            existing_channel.published_at = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )
            existing_channel.thumbnails = snippet.get("thumbnails", {})
            existing_channel.is_own_channel = is_own or existing_channel.is_own_channel
            existing_channel.updated_at = datetime.utcnow()
            self.db.add(existing_channel)
            await self.db.commit()
            await self.db.refresh(existing_channel)
            return existing_channel

        # Create new channel
        channel = Channel(
            youtube_channel_id=youtube_channel_id,
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            custom_url=snippet.get("customUrl"),
            country=snippet.get("country"),
            published_at=datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            ),
            thumbnails=snippet.get("thumbnails", {}),
            is_own_channel=is_own,
        )

        self.db.add(channel)
        await self.db.commit()
        await self.db.refresh(channel)

        # Create initial stats snapshot
        await self.create_stats_snapshot(channel.id, statistics)

        return channel

    async def create_stats_snapshot(
        self,
        channel_id: int,
        statistics: dict,
        source: str = "manual"
    ) -> ChannelStatsSnapshot:
        """
        Create a statistics snapshot for a channel.

        Args:
            channel_id: Internal channel ID
            statistics: Statistics dict from YouTube API
            source: Source of snapshot (manual, daily_cron, etc.)

        Returns:
            Created ChannelStatsSnapshot
        """
        snapshot = ChannelStatsSnapshot(
            channel_id=channel_id,
            view_count=int(statistics.get("viewCount", 0)),
            subscriber_count=int(statistics.get("subscriberCount", 0))
            if not statistics.get("hiddenSubscriberCount", False)
            else None,
            video_count=int(statistics.get("videoCount", 0)),
            source=source,
        )

        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def update_channel_stats(self, channel_id: int) -> Optional[ChannelStatsSnapshot]:
        """
        Update statistics for an existing channel.

        Args:
            channel_id: Internal channel ID

        Returns:
            Created ChannelStatsSnapshot or None if channel not found
        """
        # Get channel
        stmt = select(Channel).where(Channel.id == channel_id)
        result = await self.db.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            return None

        # Fetch latest data from YouTube
        channel_data = await self.youtube.get_channel_by_id(channel.youtube_channel_id)
        if not channel_data:
            return None

        statistics = channel_data.get("statistics", {})
        return await self.create_stats_snapshot(
            channel_id,
            statistics,
            source="daily_cron"
        )

    async def get_all_channels(self) -> List[Channel]:
        """Get all channels from database"""
        stmt = select(Channel)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
