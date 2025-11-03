"""
Celery application configuration for background tasks.
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery app
celery_app = Celery(
    "youtube_analytics",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.import_tasks",
        "app.tasks.update_tasks",
        "app.tasks.alert_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "update-all-channels-daily": {
        "task": "app.tasks.update_tasks.update_all_channels",
        "schedule": crontab(
            hour=settings.UPDATE_STATS_CRON_HOUR,
            minute=0,
        ),
    },
    "check-alerts-periodic": {
        "task": "app.tasks.alert_tasks.check_all_alerts",
        "schedule": crontab(
            minute=f"*/{settings.CHECK_ALERTS_INTERVAL_MINUTES}",
        ),
    },
}
