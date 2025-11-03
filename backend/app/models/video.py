"""Video and video statistics models"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON, Index
from sqlalchemy import BigInteger


class Video(SQLModel, table=True):
    """YouTube video metadata"""

    __tablename__ = "videos"
    __table_args__ = (
        Index("idx_videos_youtube_id", "youtube_video_id"),
        Index("idx_videos_channel_id", "channel_id"),
        Index("idx_videos_published_at", "published_at"),
        Index("idx_videos_status", "status"),
        Index("idx_videos_channel_published", "channel_id", "published_at"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    youtube_video_id: str = Field(
        max_length=255,
        unique=True,
        index=True,
        nullable=False,
        description="YouTube video ID (11 characters)"
    )
    channel_id: int = Field(
        foreign_key="channels.id",
        nullable=False,
        index=True,
        sa_column=Column(BigInteger)
    )
    title: str = Field(max_length=500, nullable=False)
    description: Optional[str] = None
    tags: Optional[list] = Field(default=None, sa_column=Column(JSON))
    category_id: Optional[str] = Field(default=None, max_length=50)
    duration_seconds: Optional[int] = None
    published_at: datetime = Field(nullable=False, index=True)
    status: Optional[str] = Field(default=None, max_length=50)
    thumbnails: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    definition: Optional[str] = Field(default=None, max_length=10)
    dimension: Optional[str] = Field(default=None, max_length=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VideoStatsSnapshot(SQLModel, table=True):
    """Video statistics snapshot (time-series data)"""

    __tablename__ = "video_stats_snapshots"
    __table_args__ = (
        Index("idx_video_stats_video_captured", "video_id", "captured_at"),
        Index("idx_video_stats_view_count", "view_count"),
        # Note: Partitioning will be set up in Alembic migration
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    video_id: int = Field(
        foreign_key="videos.id",
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
    like_count: int = Field(default=0, sa_column=Column(BigInteger))
    comment_count: int = Field(default=0, sa_column=Column(BigInteger))
    favorite_count: int = Field(default=0, sa_column=Column(BigInteger))
    source: str = Field(default="daily_cron", max_length=50)
