"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


# Create Celery app
celery_app = Celery(
    "youtube_analytics",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "update-channel-stats-daily": {
        "task": "app.tasks.snapshot_tasks.update_all_channel_stats",
        "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
    },
    "update-video-stats-daily": {
        "task": "app.tasks.snapshot_tasks.update_all_video_stats",
        "schedule": crontab(hour=3, minute=0),  # 3 AM UTC daily
    },
    "check-alerts": {
        "task": "app.tasks.alert_tasks.check_all_alerts",
        "schedule": crontab(hour="*/6", minute=0),  # Every 6 hours
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
