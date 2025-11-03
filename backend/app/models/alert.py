"""Alert and notification models"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON, Index
from sqlalchemy import BigInteger


class AlertRule(SQLModel, table=True):
    """Configurable alert rule"""

    __tablename__ = "alert_rules"
    __table_args__ = (
        Index("idx_alert_rules_type", "type"),
        Index("idx_alert_rules_is_active", "is_active"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    name: str = Field(max_length=255, nullable=False)
    description: Optional[str] = None
    type: str = Field(
        max_length=100,
        nullable=False,
        index=True,
        description="Alert type: video_views_growth, channel_activity_drop, high_engagement, etc."
    )
    params: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Alert parameters: {threshold: 10000, period_hours: 24, channel_ids: [1,2]}"
    )
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    """Triggered alert from an alert rule"""

    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_rule_id", "alert_rule_id"),
        Index("idx_alerts_entity", "entity_type", "entity_id"),
        Index("idx_alerts_triggered_at", "triggered_at"),
        Index("idx_alerts_status", "status"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    alert_rule_id: int = Field(
        foreign_key="alert_rules.id",
        nullable=False,
        index=True,
        sa_column=Column(BigInteger)
    )
    entity_type: str = Field(
        max_length=50,
        nullable=False,
        description="Entity type: video or channel"
    )
    entity_id: int = Field(
        nullable=False,
        sa_column=Column(BigInteger),
        description="References videos.id or channels.id"
    )
    triggered_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True
    )
    payload: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Detailed event data: {old_value: 1000, new_value: 15000, delta: 14000}"
    )
    status: str = Field(
        default="new",
        max_length=50,
        index=True,
        description="Status: new, read, archived"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationTarget(SQLModel, table=True):
    """External notification endpoint (webhook, Telegram, etc.)"""

    __tablename__ = "notification_targets"
    __table_args__ = (
        Index("idx_notification_targets_type", "type"),
        Index("idx_notification_targets_is_active", "is_active"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    name: str = Field(max_length=255, nullable=False)
    type: str = Field(
        max_length=50,
        nullable=False,
        index=True,
        description="Notification type: webhook, telegram, slack, email"
    )
    config: dict = Field(
        sa_column=Column(JSON, nullable=False),
        description="Configuration: {url: '...', token: '...', chat_id: '...'}"
    )
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AlertRuleNotification(SQLModel, table=True):
    """Many-to-many relationship between alert rules and notification targets"""

    __tablename__ = "alert_rule_notifications"

    alert_rule_id: int = Field(
        foreign_key="alert_rules.id",
        primary_key=True,
        sa_column=Column(BigInteger)
    )
    notification_target_id: int = Field(
        foreign_key="notification_targets.id",
        primary_key=True,
        sa_column=Column(BigInteger)
    )
