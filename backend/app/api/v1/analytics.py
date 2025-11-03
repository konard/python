"""Analytics API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/compare")
async def compare_channels():
    """Compare multiple channels."""
    return {"comparison": {}}


@router.get("/metrics")
async def get_metrics():
    """Get aggregated metrics."""
    return {"metrics": {}}
