"""Video API endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.video import Video
from app.services.data_ingestion.video_service import VideoIngestionService


router = APIRouter()


# Pydantic schemas
class VideoResponse(BaseModel):
    """Schema for video response"""
    id: int
    youtube_video_id: str
    channel_id: int
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    published_at: datetime
    status: Optional[str] = None
    thumbnails: Optional[dict] = None

    class Config:
        from_attributes = True


@router.get("/channels/{channel_id}/videos", response_model=List[VideoResponse])
async def list_channel_videos(
    channel_id: int,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List videos for a channel.

    Query parameters:
    - limit: Maximum number of videos to return (max 200)
    - offset: Number of videos to skip
    """
    service = VideoIngestionService(db)
    videos = await service.get_channel_videos(channel_id, limit=limit, offset=offset)
    return videos


@router.post("/channels/{channel_id}/import-videos")
async def import_channel_videos(
    channel_id: int,
    max_videos: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Import all videos from a channel.

    This may take a while for channels with many videos.
    Consider using this as a background task in production.

    Query parameters:
    - max_videos: Maximum number of videos to import (None = all)
    """
    service = VideoIngestionService(db)
    videos = await service.import_channel_videos(channel_id, max_videos=max_videos)

    return {
        "message": "Videos imported successfully",
        "count": len(videos),
        "channel_id": channel_id
    }


@router.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get video details by ID"""
    from sqlmodel import select

    stmt = select(Video).where(Video.id == video_id)
    result = await db.execute(stmt)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )

    return video


@router.post("/videos/{video_id}/update-stats")
async def update_video_stats(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger stats update for a video"""
    service = VideoIngestionService(db)
    snapshot = await service.update_video_stats(video_id)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )

    return {
        "message": "Stats updated successfully",
        "snapshot": {
            "captured_at": snapshot.captured_at.isoformat(),
            "view_count": snapshot.view_count,
            "like_count": snapshot.like_count,
            "comment_count": snapshot.comment_count
        }
    }
