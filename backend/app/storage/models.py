"""
SQLAlchemy ORM models for the YouTube Analytics system.
All models use async SQLAlchemy 2.0 syntax.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.storage.database import Base


class Channel(Base):
    """YouTube channel information."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    youtube_channel_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    custom_url: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(10))
    thumbnails: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_own_channel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    videos: Mapped[List["Video"]] = relationship(
        "Video", back_populates="channel", cascade="all, delete-orphan"
    )
    stats_snapshots: Mapped[List["ChannelStatsSnapshot"]] = relationship(
        "ChannelStatsSnapshot", back_populates="channel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, title='{self.title}', youtube_id='{self.youtube_channel_id}')>"


class Video(Base):
    """YouTube video information."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    youtube_video_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[dict]] = mapped_column(JSONB)
    category_id: Mapped[Optional[str]] = mapped_column(String(50))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    thumbnails: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="videos")
    stats_snapshots: Mapped[List["VideoStatsSnapshot"]] = relationship(
        "VideoStatsSnapshot", back_populates="video", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="video", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_videos_channel_published", "channel_id", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title='{self.title}', youtube_id='{self.youtube_video_id}')>"


class ChannelStatsSnapshot(Base):
    """Snapshot of channel statistics at a specific point in time."""

    __tablename__ = "channel_stats_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    view_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    subscriber_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    hidden_subscriber_count: Mapped[bool] = mapped_column(Boolean, default=False)
    video_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="stats_snapshots")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("channel_id", "captured_at", name="uq_channel_stats_snapshot"),
        Index("ix_channel_stats_captured_desc", "channel_id", captured_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<ChannelStatsSnapshot(channel_id={self.channel_id}, captured_at={self.captured_at})>"


class VideoStatsSnapshot(Base):
    """Snapshot of video statistics at a specific point in time."""

    __tablename__ = "video_stats_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    view_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    like_count: Mapped[Optional[int]] = mapped_column(Integer)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer)
    favorite_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="stats_snapshots")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("video_id", "captured_at", name="uq_video_stats_snapshot"),
        Index("ix_video_stats_captured_desc", "video_id", captured_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<VideoStatsSnapshot(video_id={self.video_id}, captured_at={self.captured_at})>"


class Comment(Base):
    """YouTube comment on a video."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    youtube_comment_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_channel_id: Mapped[Optional[str]] = mapped_column(String(255))
    text_original: Mapped[Optional[str]] = mapped_column(Text)
    like_count: Mapped[Optional[int]] = mapped_column(Integer)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    # Future AI fields
    sentiment_score: Mapped[Optional[float]] = mapped_column(JSONB)  # Can be expanded
    topic_tags: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="comments")

    # Indexes
    __table_args__ = (
        Index("ix_comments_video_published", "video_id", published_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, video_id={self.video_id}, youtube_id='{self.youtube_comment_id}')>"


class AlertRule(Base):
    """Alert rule configuration."""

    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # params structure depends on rule type:
    # video_views_growth: {"threshold": 10000, "period_hours": 24, "channel_ids": [1,2]}
    # channel_activity_drop: {"threshold_percent": 50, "period_days": 7, "channel_ids": [1]}
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="alert_rule", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AlertRule(id={self.id}, name='{self.name}', type='{self.type}')>"


class Alert(Base):
    """Triggered alert instance."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'video' or 'channel'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    # payload contains details about what triggered the alert
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="new", nullable=False, index=True)  # 'new', 'read', 'dismissed'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    alert_rule: Mapped["AlertRule"] = relationship("AlertRule", back_populates="alerts")

    # Indexes
    __table_args__ = (
        Index("ix_alerts_status_triggered", "status", triggered_at.desc()),
        Index("ix_alerts_entity", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.entity_type}, entity_id={self.entity_id}, status='{self.status}')>"


class NotificationTarget(Base):
    """Notification target configuration for future integrations."""

    __tablename__ = "notification_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'internal', 'webhook', 'telegram', etc.
    # config structure depends on type:
    # webhook: {"url": "https://...", "headers": {}}
    # telegram: {"bot_token": "...", "chat_id": "..."}
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<NotificationTarget(id={self.id}, type='{self.type}', active={self.is_active})>"
