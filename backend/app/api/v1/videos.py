"""Video API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_videos():
    """List videos with filtering and sorting."""
    return {"items": [], "total": 0}


@router.get("/{video_id}")
async def get_video(video_id: int):
    """Get video details and statistics over time."""
    return {"id": video_id, "title": "TODO"}


@router.get("/{video_id}/stats")
async def get_video_stats(video_id: int):
    """Get video statistics timeline."""
    return {"video_id": video_id, "snapshots": []}


@router.get("/{video_id}/comments")
async def get_video_comments(video_id: int):
    """Get video comments."""
    return {"video_id": video_id, "comments": []}
