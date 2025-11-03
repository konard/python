"""
Background scheduler using APScheduler for periodic tasks.
This replaces Celery for the MVP version - simpler setup with no Redis dependency.
"""
import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.channel import Channel
from app.models.video import Video
from app.services.data_ingestion.channel_service import ChannelIngestionService
from app.services.data_ingestion.video_service import VideoIngestionService
from app.services.data_ingestion.youtube_client import get_youtube_client
from app.services.alerts.alert_service import AlertService


class BackgroundScheduler:
    """
    Background scheduler for periodic data collection and alerts.

    Uses APScheduler for simplicity in MVP.
    Can be upgraded to Celery + Redis for production.
    """

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.youtube_client = get_youtube_client()

    async def update_all_channel_stats(self):
        """
        Update statistics for all channels.
        Scheduled to run daily at 2 AM (configurable).
        """
        print(f"[{datetime.now()}] Starting scheduled channel stats update...")

        db = SessionLocal()
        try:
            # Get all channels
            stmt = select(Channel)
            result = db.execute(stmt)
            channels = list(result.scalars().all())

            print(f"Found {len(channels)} channels to update")

            channel_service = ChannelIngestionService(db)
            updated_count = 0

            for channel in channels:
                try:
                    print(f"Updating stats for channel: {channel.title}")
                    await channel_service.update_channel_stats(channel.id)
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating channel {channel.id}: {e}")

            print(f"Channel stats update completed: {updated_count}/{len(channels)} updated")

        except Exception as e:
            print(f"Error in update_all_channel_stats: {e}")
        finally:
            db.close()

    async def update_all_video_stats(self):
        """
        Update statistics for all videos (recent ones prioritized).
        Scheduled to run daily at 3 AM.

        Strategy:
        - Recent videos (< 7 days old): update daily
        - Older videos can be updated less frequently (handled by limiting query)
        """
        print(f"[{datetime.now()}] Starting scheduled video stats update...")

        db = SessionLocal()
        try:
            # Get recent videos (last 30 days) - prioritize active content
            # In production, implement tiered update strategy
            stmt = (
                select(Video)
                .order_by(Video.published_at.desc())
                .limit(500)  # Limit to avoid quota exhaustion
            )
            result = db.execute(stmt)
            videos = list(result.scalars().all())

            print(f"Found {len(videos)} videos to update")

            video_service = VideoIngestionService(db)
            updated_count = 0

            for video in videos:
                try:
                    print(f"Updating stats for video: {video.title[:50]}...")
                    await video_service.update_video_stats(video.youtube_video_id)
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating video {video.id}: {e}")

            print(f"Video stats update completed: {updated_count}/{len(videos)} updated")

        except Exception as e:
            print(f"Error in update_all_video_stats: {e}")
        finally:
            db.close()

    async def check_all_alerts(self):
        """
        Check all alert rules and trigger alerts.
        Scheduled to run every 6 hours.
        """
        print(f"[{datetime.now()}] Starting alert check...")

        db = SessionLocal()
        try:
            alert_service = AlertService(db)
            triggered_alerts = await alert_service.check_all_alert_rules()

            print(f"Alert check completed: {len(triggered_alerts)} alerts triggered")

        except Exception as e:
            print(f"Error in check_all_alerts: {e}")
        finally:
            db.close()

    def start(self):
        """Start the background scheduler"""
        if self.scheduler is not None:
            print("Scheduler is already running")
            return

        self.scheduler = AsyncIOScheduler()

        # Parse cron schedule from config (default: "0 2 * * *" = 2 AM daily)
        try:
            cron_parts = settings.snapshot_schedule_cron.split()
            if len(cron_parts) >= 5:
                # Parse cron: minute hour day month day_of_week
                trigger_channels = CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4],
                )
            else:
                # Default to 2 AM daily
                trigger_channels = CronTrigger(hour=2, minute=0)
        except Exception as e:
            print(f"Error parsing cron schedule: {e}, using default (2 AM daily)")
            trigger_channels = CronTrigger(hour=2, minute=0)

        # Schedule channel stats update (2 AM daily by default)
        self.scheduler.add_job(
            self.update_all_channel_stats,
            trigger=trigger_channels,
            id='update_channel_stats',
            name='Update all channel statistics',
            replace_existing=True
        )

        # Schedule video stats update (3 AM daily)
        self.scheduler.add_job(
            self.update_all_video_stats,
            trigger=CronTrigger(hour=3, minute=0),
            id='update_video_stats',
            name='Update all video statistics',
            replace_existing=True
        )

        # Schedule alert checks (every 6 hours)
        self.scheduler.add_job(
            self.check_all_alerts,
            trigger='interval',
            hours=6,
            id='check_alerts',
            name='Check alert rules',
            replace_existing=True
        )

        self.scheduler.start()
        print("Background scheduler started successfully")
        print(f"Channel stats update scheduled: {trigger_channels}")
        print("Video stats update scheduled: Daily at 3:00 AM")
        print("Alert checks scheduled: Every 6 hours")

    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler is not None:
            self.scheduler.shutdown()
            self.scheduler = None
            print("Background scheduler stopped")


# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def shutdown_scheduler():
    """Shutdown the global scheduler"""
    scheduler = get_scheduler()
    scheduler.shutdown()
