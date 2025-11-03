"""
Channel management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl

from app.storage.database import get_db
from app.data_ingestion.youtube_client import YouTubeAPIClient
from app.data_ingestion.channel_parser import ChannelURLParser

router = APIRouter()


# Pydantic schemas
class ChannelCreate(BaseModel):
    """Schema for creating a new channel."""
    url: str
    is_own_channel: bool = False


class ChannelResponse(BaseModel):
    """Schema for channel response."""
    id: int
    youtube_channel_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    custom_url: Optional[str] = None
    country: Optional[str] = None
    is_own_channel: bool
    subscriber_count: Optional[int] = None
    view_count: Optional[int] = None
    video_count: Optional[int] = None

    class Config:
        from_attributes = True


class ChannelListResponse(BaseModel):
    """Schema for channel list response."""
    items: List[ChannelResponse]
    total: int
    page: int
    page_size: int


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new channel by URL.

    Accepts various YouTube URL formats:
    - https://www.youtube.com/@username
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/user/username
    - Video URLs (extracts channel from video)

    Triggers background task to import channel videos.
    """
    try:
        # Parse the URL
        parsed = ChannelURLParser.parse(channel_data.url)

        # Initialize YouTube client
        youtube = YouTubeAPIClient()

        # Get channel data based on parsed type
        if parsed["type"] == "channel_id":
            channel_info = await youtube.get_channel_by_id(parsed["id"])
        elif parsed["type"] in ["handle", "user"]:
            channel_info = await youtube.get_channel_by_username(parsed["id"])
        elif parsed["type"] == "video":
            # Get channel from video
            videos = await youtube.get_videos_details([parsed["id"]])
            if videos:
                channel_id = videos[0]["snippet"]["channelId"]
                channel_info = await youtube.get_channel_by_id(channel_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported URL format"
            )

        if not channel_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )

        # TODO: Save channel to database
        # TODO: Trigger background task to import videos

        # Return mock response for now
        return ChannelResponse(
            id=1,
            youtube_channel_id=channel_info["id"],
            title=channel_info["snippet"]["title"],
            description=channel_info["snippet"].get("description"),
            custom_url=channel_info["snippet"].get("customUrl"),
            country=channel_info["snippet"].get("country"),
            is_own_channel=channel_data.is_own_channel,
            subscriber_count=int(channel_info["statistics"].get("subscriberCount", 0) or 0),
            view_count=int(channel_info["statistics"].get("viewCount", 0) or 0),
            video_count=int(channel_info["statistics"].get("videoCount", 0) or 0),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add channel: {str(e)}"
        )


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    skip: int = 0,
    limit: int = 20,
    is_own: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all channels with optional filtering.

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - is_own: Filter by ownership (true for own channels, false for competitors)
    """
    # TODO: Implement database query
    return ChannelListResponse(
        items=[],
        total=0,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific channel."""
    # TODO: Implement database query
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Channel not found"
    )


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    is_own_channel: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update channel settings."""
    # TODO: Implement update logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Channel not found"
    )


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a channel and all associated data."""
    # TODO: Implement delete logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Channel not found"
    )


@router.post("/{channel_id}/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger manual refresh of channel data.
    Returns 202 Accepted as the task runs in background.
    """
    # TODO: Trigger Celery task
    return {"message": "Refresh task queued", "channel_id": channel_id}
