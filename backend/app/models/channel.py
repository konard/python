"""Channel and channel statistics models"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON, Index
from sqlalchemy import BigInteger


class Channel(SQLModel, table=True):
    """YouTube channel information"""

    __tablename__ = "channels"
    __table_args__ = (
        Index("idx_channels_youtube_id", "youtube_channel_id"),
        Index("idx_channels_is_own", "is_own_channel"),
        Index("idx_channels_created_at", "created_at"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    youtube_channel_id: str = Field(
        max_length=255,
        unique=True,
        index=True,
        nullable=False,
        description="YouTube channel ID (e.g., UCxxxxxxxx)"
    )
    title: str = Field(max_length=500, nullable=False)
    description: Optional[str] = Field(default=None, sa_column=Column(JSON))
    custom_url: Optional[str] = Field(default=None, max_length=255)
    country: Optional[str] = Field(default=None, max_length=10)
    published_at: Optional[datetime] = None
    thumbnails: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    is_own_channel: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChannelStatsSnapshot(SQLModel, table=True):
    """Channel statistics snapshot (time-series data)"""

    __tablename__ = "channel_stats_snapshots"
    __table_args__ = (
        Index("idx_channel_stats_channel_captured", "channel_id", "captured_at"),
        # Note: Partitioning will be set up in Alembic migration
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    channel_id: int = Field(
        foreign_key="channels.id",
        nullable=False,
        index=True,
        sa_column=Column(BigInteger)
    )
    captured_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True
    )
    view_count: int = Field(default=0, sa_column=Column(BigInteger))
    subscriber_count: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    video_count: int = Field(default=0)
    source: str = Field(default="daily_cron", max_length=50)
