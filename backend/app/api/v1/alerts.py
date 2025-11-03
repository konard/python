"""Alert API endpoints"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.alert import AlertRule, Alert
from app.services.alerts.alert_service import AlertService


router = APIRouter()


# Pydantic schemas
class AlertRuleCreate(BaseModel):
    """Schema for creating an alert rule"""
    name: str
    description: str
    type: str
    params: Dict[str, Any]


class AlertRuleResponse(BaseModel):
    """Schema for alert rule response"""
    id: int
    name: str
    description: Optional[str] = None
    type: str
    params: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: int
    alert_rule_id: int
    entity_type: str
    entity_id: int
    triggered_at: str
    payload: Dict[str, Any]
    status: str

    class Config:
        from_attributes = True


@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new alert rule.

    Supported alert types:
    - video_views_growth: Trigger when video views increase by threshold
    - channel_activity_drop: Trigger when channel activity drops
    - high_engagement: Trigger when video has high engagement rate

    Example params:
    {
        "threshold": 10000,
        "period_hours": 24,
        "channel_ids": [1, 2, 3]
    }
    """
    service = AlertService(db)
    rule = await service.create_alert_rule(
        name=rule_data.name,
        description=rule_data.description,
        alert_type=rule_data.type,
        params=rule_data.params
    )
    return rule


@router.get("/alert-rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    active_only: bool = Query(default=True),
    db: AsyncSession = Depends(get_db)
):
    """
    List alert rules.

    Query parameters:
    - active_only: Only return active rules (default: true)
    """
    if active_only:
        service = AlertService(db)
        rules = await service.get_active_alert_rules()
    else:
        from sqlmodel import select
        stmt = select(AlertRule)
        result = await db.execute(stmt)
        rules = list(result.scalars().all())

    return rules


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    List triggered alerts.

    Query parameters:
    - status: Filter by status (new, read, archived)
    - limit: Maximum number of alerts to return (max 500)
    """
    service = AlertService(db)
    alerts = await service.get_active_alerts(status=status_filter, limit=limit)

    return [
        AlertResponse(
            id=alert.id,
            alert_rule_id=alert.alert_rule_id,
            entity_type=alert.entity_type,
            entity_id=alert.entity_id,
            triggered_at=alert.triggered_at.isoformat(),
            payload=alert.payload,
            status=alert.status
        )
        for alert in alerts
    ]


@router.patch("/alerts/{alert_id}/mark-read")
async def mark_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark an alert as read"""
    service = AlertService(db)
    alert = await service.mark_alert_read(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )

    return {
        "message": "Alert marked as read",
        "alert_id": alert_id
    }
