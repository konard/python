"""Analytics API endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.services.analytics.metrics import MetricsService


router = APIRouter()


@router.get("/analytics/videos/{video_id}/metrics")
async def get_video_metrics(
    video_id: int,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive metrics for a video.

    Includes:
    - Current stats (views, likes, comments)
    - Calculated metrics (engagement rate, views per day)
    - Growth metrics (24h, 7d deltas)

    Query parameters:
    - from_date: Start date for analysis (ISO format)
    - to_date: End date for analysis (ISO format)
    """
    service = MetricsService(db)
    metrics = await service.calculate_video_metrics(video_id, from_date, to_date)

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"Video {video_id} not found"
        )

    return metrics


@router.get("/analytics/channels/{channel_id}/metrics")
async def get_channel_metrics(
    channel_id: int,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive metrics for a channel.

    Includes:
    - Current stats (total views, subscribers, video count)
    - Average video performance
    - Growth metrics (7d, 30d deltas)

    Query parameters:
    - from_date: Start date for analysis (ISO format)
    - to_date: End date for analysis (ISO format)
    """
    service = MetricsService(db)
    metrics = await service.calculate_channel_metrics(channel_id, from_date, to_date)

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"Channel {channel_id} not found"
        )

    return metrics


@router.get("/analytics/trending/videos")
async def get_trending_videos(
    channel_id: Optional[int] = None,
    limit: int = Query(default=20, le=100),
    period_hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trending videos (highest view growth).

    Query parameters:
    - channel_id: Filter by specific channel (optional)
    - limit: Maximum number of videos to return (max 100)
    - period_hours: Time period for trend calculation (1-168 hours)
    """
    service = MetricsService(db)
    trending = await service.get_trending_videos(
        channel_id=channel_id,
        limit=limit,
        period_hours=period_hours
    )

    return {
        "period_hours": period_hours,
        "count": len(trending),
        "videos": trending
    }


@router.get("/analytics/compare/channels")
async def compare_channels(
    channel_ids: str = Query(..., description="Comma-separated channel IDs"),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare multiple channels.

    Query parameters:
    - channel_ids: Comma-separated list of channel IDs (e.g., "1,2,3")
    - from_date: Start date for comparison (ISO format)
    - to_date: End date for comparison (ISO format)
    """
    try:
        ids = [int(id.strip()) for id in channel_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid channel_ids format. Use comma-separated integers."
        )

    if len(ids) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 channels can be compared at once"
        )

    service = MetricsService(db)
    comparison = []

    for channel_id in ids:
        metrics = await service.calculate_channel_metrics(channel_id, from_date, to_date)
        if metrics:
            comparison.append(metrics)

    return {
        "channels": comparison,
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None
    }
