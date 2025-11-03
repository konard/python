"""Trending videos API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/videos")
async def get_trending_videos():
    """Get trending videos across all channels."""
    return {"videos": []}
