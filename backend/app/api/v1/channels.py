"""Channel API endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.channel import Channel
from app.services.data_ingestion.channel_service import ChannelIngestionService


router = APIRouter()


# Pydantic schemas
class ChannelCreate(BaseModel):
    """Schema for creating a channel"""
    url: str
    is_own_channel: bool = False


class ChannelResponse(BaseModel):
    """Schema for channel response"""
    id: int
    youtube_channel_id: str
    title: str
    description: Optional[str] = None
    custom_url: Optional[str] = None
    country: Optional[str] = None
    is_own_channel: bool
    thumbnails: Optional[dict] = None

    class Config:
        from_attributes = True


@router.post("/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new channel by URL.

    Accepts YouTube channel URLs in various formats:
    - https://www.youtube.com/@handle
    - https://www.youtube.com/channel/UCxxxxx
    - https://www.youtube.com/c/customname
    - https://www.youtube.com/user/username
    - https://www.youtube.com/watch?v=videoid (extracts channel from video)
    """
    service = ChannelIngestionService(db)
    channel = await service.add_channel_by_url(
        channel_data.url,
        is_own=channel_data.is_own_channel
    )

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find channel from provided URL"
        )

    # TODO: Trigger background task to import videos
    # from app.tasks.snapshot_tasks import import_channel_videos
    # import_channel_videos.delay(channel.id)

    return channel


@router.get("/channels", response_model=List[ChannelResponse])
async def list_channels(
    is_own: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all channels.

    Query parameters:
    - is_own: Filter by own channels (true/false)
    """
    service = ChannelIngestionService(db)
    channels = await service.get_all_channels()

    if is_own is not None:
        channels = [c for c in channels if c.is_own_channel == is_own]

    return channels


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get channel details by ID"""
    from sqlmodel import select

    stmt = select(Channel).where(Channel.id == channel_id)
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )

    return channel


@router.post("/channels/{channel_id}/update-stats")
async def update_channel_stats(
    channel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger stats update for a channel"""
    service = ChannelIngestionService(db)
    snapshot = await service.update_channel_stats(channel_id)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )

    return {
        "message": "Stats updated successfully",
        "snapshot": {
            "captured_at": snapshot.captured_at.isoformat(),
            "view_count": snapshot.view_count,
            "subscriber_count": snapshot.subscriber_count,
            "video_count": snapshot.video_count
        }
    }
