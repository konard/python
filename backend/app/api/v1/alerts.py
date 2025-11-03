"""Alert API endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_alerts():
    """List triggered alerts."""
    return {"alerts": []}


@router.get("/{alert_id}")
async def get_alert(alert_id: int):
    """Get alert details."""
    return {"id": alert_id}


@router.put("/{alert_id}")
async def update_alert(alert_id: int):
    """Update alert status (mark as read/dismissed)."""
    return {"id": alert_id, "status": "read"}


@router.get("/rules")
async def list_alert_rules():
    """List alert rules."""
    return {"rules": []}


@router.post("/rules")
async def create_alert_rule():
    """Create new alert rule."""
    return {"id": 1}


@router.put("/rules/{rule_id}")
async def update_alert_rule(rule_id: int):
    """Update alert rule."""
    return {"id": rule_id}


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: int):
    """Delete alert rule."""
    return {"message": "Deleted"}
