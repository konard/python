"""Service for managing and checking alert rules"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertRule, Alert
from app.models.video import VideoStatsSnapshot
from app.models.channel import ChannelStatsSnapshot


class AlertService:
    """Service for managing alerts and checking rules"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert_rule(
        self,
        name: str,
        description: str,
        alert_type: str,
        params: Dict[str, Any]
    ) -> AlertRule:
        """
        Create a new alert rule.

        Args:
            name: Rule name
            description: Rule description
            alert_type: Type of alert (video_views_growth, channel_activity_drop, etc.)
            params: Rule parameters (thresholds, filters, etc.)

        Returns:
            Created AlertRule
        """
        rule = AlertRule(
            name=name,
            description=description,
            type=alert_type,
            params=params,
            is_active=True
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def check_video_views_growth_rule(
        self,
        rule: AlertRule
    ) -> List[Alert]:
        """
        Check if any videos have exceeded view growth threshold.

        Rule params:
        - threshold: Minimum view delta to trigger alert
        - period_hours: Time period for comparison (default 24)
        - channel_ids: Optional list of channel IDs to filter
        """
        threshold = rule.params.get("threshold", 10000)
        period_hours = rule.params.get("period_hours", 24)
        channel_ids = rule.params.get("channel_ids")

        cutoff_time = datetime.utcnow() - timedelta(hours=period_hours)
        triggered_alerts = []

        # This is simplified - in production, use optimized queries
        # or materialized views

        # Get recent snapshots and compare
        # ... implementation would check growth and create alerts

        return triggered_alerts

    async def check_channel_activity_drop_rule(
        self,
        rule: AlertRule
    ) -> List[Alert]:
        """
        Check if any channels have experienced activity drops.

        Rule params:
        - threshold_percent: Minimum percentage drop to trigger alert
        - metric: Which metric to monitor (views, subscribers, videos)
        - period_days: Time period for comparison
        - channel_ids: Optional list of channel IDs to filter
        """
        threshold_percent = rule.params.get("threshold_percent", 20)
        metric = rule.params.get("metric", "views")
        period_days = rule.params.get("period_days", 7)
        channel_ids = rule.params.get("channel_ids")

        triggered_alerts = []

        # Implementation would check for drops and create alerts

        return triggered_alerts

    async def check_high_engagement_rule(
        self,
        rule: AlertRule
    ) -> List[Alert]:
        """
        Check if any videos have unusually high engagement.

        Rule params:
        - engagement_threshold: Minimum engagement rate (percent)
        - min_views: Minimum views to qualify
        - channel_ids: Optional list of channel IDs to filter
        """
        engagement_threshold = rule.params.get("engagement_threshold", 10)
        min_views = rule.params.get("min_views", 1000)
        channel_ids = rule.params.get("channel_ids")

        triggered_alerts = []

        # Implementation would check engagement rates and create alerts

        return triggered_alerts

    async def trigger_alert(
        self,
        rule_id: int,
        entity_type: str,
        entity_id: int,
        payload: Dict[str, Any]
    ) -> Alert:
        """
        Create a triggered alert.

        Args:
            rule_id: Alert rule ID
            entity_type: Type of entity (video or channel)
            entity_id: Entity ID
            payload: Alert payload with details

        Returns:
            Created Alert
        """
        alert = Alert(
            alert_rule_id=rule_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            status="new"
        )

        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_active_alerts(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get active alerts.

        Args:
            status: Filter by status (None = all)
            limit: Maximum number of alerts to return

        Returns:
            List of alerts
        """
        stmt = select(Alert).order_by(Alert.triggered_at.desc()).limit(limit)

        if status:
            stmt = stmt.where(Alert.status == status)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_alert_read(self, alert_id: int) -> Optional[Alert]:
        """Mark an alert as read"""
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await self.db.execute(stmt)
        alert = result.scalar_one_or_none()

        if alert:
            alert.status = "read"
            alert.updated_at = datetime.utcnow()
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)

        return alert

    async def get_active_alert_rules(self) -> List[AlertRule]:
        """Get all active alert rules"""
        stmt = select(AlertRule).where(AlertRule.is_active.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
