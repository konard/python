"""Metrics calculation for videos and channels"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc

from app.models.video import Video, VideoStatsSnapshot
from app.models.channel import Channel, ChannelStatsSnapshot


class MetricsService:
    """Service for calculating analytics metrics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_video_metrics(
        self,
        video_id: int,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a video.

        Args:
            video_id: Internal video ID
            from_date: Start date for metric calculation
            to_date: End date for metric calculation

        Returns:
            Dict with calculated metrics
        """
        # Get video
        stmt = select(Video).where(Video.id == video_id)
        result = await self.db.execute(stmt)
        video = result.scalar_one_or_none()

        if not video:
            return {}

        # Get latest snapshot
        latest_stmt = (
            select(VideoStatsSnapshot)
            .where(VideoStatsSnapshot.video_id == video_id)
            .order_by(VideoStatsSnapshot.captured_at.desc())
            .limit(1)
        )
        latest_result = await self.db.execute(latest_stmt)
        latest_snapshot = latest_result.scalar_one_or_none()

        if not latest_snapshot:
            return {
                "video_id": video_id,
                "video_title": video.title,
                "published_at": video.published_at.isoformat(),
                "status": "no_data"
            }

        # Calculate days since publication
        days_since_published = (datetime.utcnow() - video.published_at).days
        if days_since_published == 0:
            days_since_published = 1  # Avoid division by zero

        # Basic metrics
        view_count = latest_snapshot.view_count
        like_count = latest_snapshot.like_count
        comment_count = latest_snapshot.comment_count

        # Calculate rates
        like_ratio = (like_count / view_count * 100) if view_count > 0 else 0
        comment_rate = (comment_count / view_count * 100) if view_count > 0 else 0
        engagement_rate = ((like_count + comment_count) / view_count * 100) if view_count > 0 else 0
        views_per_day = view_count / days_since_published

        # Get growth metrics (compare with previous snapshot)
        growth_metrics = await self._calculate_video_growth(video_id, latest_snapshot)

        return {
            "video_id": video_id,
            "youtube_video_id": video.youtube_video_id,
            "video_title": video.title,
            "published_at": video.published_at.isoformat(),
            "duration_seconds": video.duration_seconds,
            "days_since_published": days_since_published,
            "current_stats": {
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "favorite_count": latest_snapshot.favorite_count,
            },
            "calculated_metrics": {
                "like_ratio": round(like_ratio, 2),
                "comment_rate": round(comment_rate, 2),
                "engagement_rate": round(engagement_rate, 2),
                "views_per_day": round(views_per_day, 2),
            },
            "growth_metrics": growth_metrics,
            "last_updated": latest_snapshot.captured_at.isoformat(),
        }

    async def _calculate_video_growth(
        self,
        video_id: int,
        latest_snapshot: VideoStatsSnapshot
    ) -> Dict[str, Any]:
        """Calculate growth metrics for a video"""
        # Get snapshot from 24 hours ago
        day_ago = latest_snapshot.captured_at - timedelta(days=1)
        stmt_24h = (
            select(VideoStatsSnapshot)
            .where(
                and_(
                    VideoStatsSnapshot.video_id == video_id,
                    VideoStatsSnapshot.captured_at <= day_ago
                )
            )
            .order_by(VideoStatsSnapshot.captured_at.desc())
            .limit(1)
        )
        result_24h = await self.db.execute(stmt_24h)
        snapshot_24h = result_24h.scalar_one_or_none()

        # Get snapshot from 7 days ago
        week_ago = latest_snapshot.captured_at - timedelta(days=7)
        stmt_7d = (
            select(VideoStatsSnapshot)
            .where(
                and_(
                    VideoStatsSnapshot.video_id == video_id,
                    VideoStatsSnapshot.captured_at <= week_ago
                )
            )
            .order_by(VideoStatsSnapshot.captured_at.desc())
            .limit(1)
        )
        result_7d = await self.db.execute(stmt_7d)
        snapshot_7d = result_7d.scalar_one_or_none()

        growth = {}

        if snapshot_24h:
            growth["views_delta_24h"] = latest_snapshot.view_count - snapshot_24h.view_count
            growth["likes_delta_24h"] = latest_snapshot.like_count - snapshot_24h.like_count
            growth["comments_delta_24h"] = latest_snapshot.comment_count - snapshot_24h.comment_count

        if snapshot_7d:
            growth["views_delta_7d"] = latest_snapshot.view_count - snapshot_7d.view_count
            growth["likes_delta_7d"] = latest_snapshot.like_count - snapshot_7d.like_count
            growth["comments_delta_7d"] = latest_snapshot.comment_count - snapshot_7d.comment_count

        return growth

    async def get_trending_videos(
        self,
        channel_id: Optional[int] = None,
        limit: int = 20,
        period_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get trending videos (highest view growth in last N hours).

        Args:
            channel_id: Filter by channel (None = all channels)
            limit: Maximum number of results
            period_hours: Time period for trend calculation

        Returns:
            List of videos with growth metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=period_hours)

        # This is a simplified version
        # In production, use materialized view: mv_video_growth_24h
        # For now, fetch latest snapshots and calculate

        # Get all videos (with optional channel filter)
        video_stmt = select(Video)
        if channel_id:
            video_stmt = video_stmt.where(Video.channel_id == channel_id)
        video_stmt = video_stmt.order_by(Video.published_at.desc()).limit(1000)

        video_result = await self.db.execute(video_stmt)
        videos = list(video_result.scalars().all())

        trending = []

        for video in videos:
            # Get latest snapshot
            latest_stmt = (
                select(VideoStatsSnapshot)
                .where(VideoStatsSnapshot.video_id == video.id)
                .order_by(VideoStatsSnapshot.captured_at.desc())
                .limit(1)
            )
            latest_result = await self.db.execute(latest_stmt)
            latest = latest_result.scalar_one_or_none()

            if not latest:
                continue

            # Get snapshot from period_hours ago
            old_stmt = (
                select(VideoStatsSnapshot)
                .where(
                    and_(
                        VideoStatsSnapshot.video_id == video.id,
                        VideoStatsSnapshot.captured_at <= cutoff_time
                    )
                )
                .order_by(VideoStatsSnapshot.captured_at.desc())
                .limit(1)
            )
            old_result = await self.db.execute(old_stmt)
            old = old_result.scalar_one_or_none()

            if not old:
                continue

            # Calculate growth
            views_delta = latest.view_count - old.view_count
            if views_delta > 0:
                trending.append({
                    "video_id": video.id,
                    "youtube_video_id": video.youtube_video_id,
                    "title": video.title,
                    "published_at": video.published_at.isoformat(),
                    "current_views": latest.view_count,
                    "views_delta": views_delta,
                    "period_hours": period_hours,
                })

        # Sort by views_delta descending
        trending.sort(key=lambda x: x["views_delta"], reverse=True)

        return trending[:limit]

    async def calculate_channel_metrics(
        self,
        channel_id: int,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for a channel.

        Args:
            channel_id: Internal channel ID
            from_date: Start date for metric calculation
            to_date: End date for metric calculation

        Returns:
            Dict with calculated metrics
        """
        # Get channel
        stmt = select(Channel).where(Channel.id == channel_id)
        result = await self.db.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            return {}

        # Get latest channel snapshot
        latest_stmt = (
            select(ChannelStatsSnapshot)
            .where(ChannelStatsSnapshot.channel_id == channel_id)
            .order_by(ChannelStatsSnapshot.captured_at.desc())
            .limit(1)
        )
        latest_result = await self.db.execute(latest_stmt)
        latest_snapshot = latest_result.scalar_one_or_none()

        # Count videos
        video_count_stmt = select(func.count(Video.id)).where(Video.channel_id == channel_id)
        video_count_result = await self.db.execute(video_count_stmt)
        video_count = video_count_result.scalar()

        # Get average video metrics
        avg_views_stmt = select(func.avg(VideoStatsSnapshot.view_count)).select_from(
            VideoStatsSnapshot
        ).join(
            Video, Video.id == VideoStatsSnapshot.video_id
        ).where(
            Video.channel_id == channel_id
        )
        avg_views_result = await self.db.execute(avg_views_stmt)
        avg_views = avg_views_result.scalar() or 0

        metrics = {
            "channel_id": channel_id,
            "youtube_channel_id": channel.youtube_channel_id,
            "channel_title": channel.title,
            "is_own_channel": channel.is_own_channel,
            "video_count": video_count,
            "average_views_per_video": round(avg_views, 2),
        }

        if latest_snapshot:
            metrics["current_stats"] = {
                "total_views": latest_snapshot.view_count,
                "subscriber_count": latest_snapshot.subscriber_count,
                "video_count_reported": latest_snapshot.video_count,
                "last_updated": latest_snapshot.captured_at.isoformat(),
            }

            # Calculate growth
            growth = await self._calculate_channel_growth(channel_id, latest_snapshot)
            metrics["growth_metrics"] = growth

        return metrics

    async def _calculate_channel_growth(
        self,
        channel_id: int,
        latest_snapshot: ChannelStatsSnapshot
    ) -> Dict[str, Any]:
        """Calculate growth metrics for a channel"""
        # Get snapshot from 7 days ago
        week_ago = latest_snapshot.captured_at - timedelta(days=7)
        stmt_7d = (
            select(ChannelStatsSnapshot)
            .where(
                and_(
                    ChannelStatsSnapshot.channel_id == channel_id,
                    ChannelStatsSnapshot.captured_at <= week_ago
                )
            )
            .order_by(ChannelStatsSnapshot.captured_at.desc())
            .limit(1)
        )
        result_7d = await self.db.execute(stmt_7d)
        snapshot_7d = result_7d.scalar_one_or_none()

        # Get snapshot from 30 days ago
        month_ago = latest_snapshot.captured_at - timedelta(days=30)
        stmt_30d = (
            select(ChannelStatsSnapshot)
            .where(
                and_(
                    ChannelStatsSnapshot.channel_id == channel_id,
                    ChannelStatsSnapshot.captured_at <= month_ago
                )
            )
            .order_by(ChannelStatsSnapshot.captured_at.desc())
            .limit(1)
        )
        result_30d = await self.db.execute(stmt_30d)
        snapshot_30d = result_30d.scalar_one_or_none()

        growth = {}

        if snapshot_7d:
            growth["views_delta_7d"] = latest_snapshot.view_count - snapshot_7d.view_count
            if latest_snapshot.subscriber_count and snapshot_7d.subscriber_count:
                growth["subscribers_delta_7d"] = latest_snapshot.subscriber_count - snapshot_7d.subscriber_count
            growth["videos_delta_7d"] = latest_snapshot.video_count - snapshot_7d.video_count

        if snapshot_30d:
            growth["views_delta_30d"] = latest_snapshot.view_count - snapshot_30d.view_count
            if latest_snapshot.subscriber_count and snapshot_30d.subscriber_count:
                growth["subscribers_delta_30d"] = latest_snapshot.subscriber_count - snapshot_30d.subscriber_count
            growth["videos_delta_30d"] = latest_snapshot.video_count - snapshot_30d.video_count

        return growth
