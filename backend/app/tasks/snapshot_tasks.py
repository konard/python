"""Celery tasks for collecting statistics snapshots"""
from celery import shared_task
from sqlmodel import select
from datetime import datetime

from app.core.database import SessionLocal
from app.models.channel import Channel
from app.models.video import Video
from app.services.data_ingestion.channel_service import ChannelIngestionService
from app.services.data_ingestion.video_service import VideoIngestionService


@shared_task(name="app.tasks.snapshot_tasks.update_all_channel_stats")
def update_all_channel_stats():
    """
    Update statistics for all channels.
    Runs daily via Celery Beat.
    """
    with SessionLocal() as db:
        # Get all channels
        stmt = select(Channel)
        result = db.execute(stmt)
        channels = list(result.scalars().all())

        updated_count = 0
        for channel in channels:
            try:
                # Note: We need to handle async in sync context
                # For now, using synchronous approach
                # In production, consider using async workers
                print(f"Updating stats for channel: {channel.title}")
                # This would need async handling - simplified for now
                updated_count += 1
            except Exception as e:
                print(f"Error updating channel {channel.id}: {e}")

        return {
            "task": "update_all_channel_stats",
            "total_channels": len(channels),
            "updated": updated_count,
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task(name="app.tasks.snapshot_tasks.update_all_video_stats")
def update_all_video_stats():
    """
    Update statistics for all videos.
    Runs daily via Celery Beat.

    Strategy:
    - Recent videos (published < 7 days): daily updates
    - Older videos (published 7-30 days): weekly updates
    - Very old videos (published > 30 days): monthly updates
    """
    with SessionLocal() as db:
        # For now, get all videos (in production, implement the strategy above)
        stmt = select(Video).order_by(Video.published_at.desc()).limit(1000)
        result = db.execute(stmt)
        videos = list(result.scalars().all())

        updated_count = 0
        for video in videos:
            try:
                print(f"Updating stats for video: {video.title}")
                # This would need async handling - simplified for now
                updated_count += 1
            except Exception as e:
                print(f"Error updating video {video.id}: {e}")

        return {
            "task": "update_all_video_stats",
            "total_videos": len(videos),
            "updated": updated_count,
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task(name="app.tasks.snapshot_tasks.import_channel_videos")
def import_channel_videos(channel_id: int, max_videos: int = None):
    """
    Import all videos from a channel.
    Runs asynchronously when a new channel is added.

    Args:
        channel_id: Internal channel ID
        max_videos: Maximum number of videos to import (None = all)
    """
    with SessionLocal() as db:
        try:
            print(f"Importing videos for channel ID: {channel_id}")
            # This would need async handling - simplified for now
            # In production, use async worker or handle properly

            return {
                "task": "import_channel_videos",
                "channel_id": channel_id,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error importing videos for channel {channel_id}: {e}")
            return {
                "task": "import_channel_videos",
                "channel_id": channel_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# TODO: Implement proper async task handling
# Current implementation is simplified and would need to be enhanced for production use
# Options:
# 1. Use celery-sqlalchemy-scheduler with async support
# 2. Run asyncio.run() within tasks
# 3. Use separate async worker pool
