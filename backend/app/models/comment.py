"""Comment model for YouTube video comments"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlmodel import SQLModel, Field, Column, JSON, Index
from sqlalchemy import BigInteger


class Comment(SQLModel, table=True):
    """YouTube video comment"""

    __tablename__ = "comments"
    __table_args__ = (
        Index("idx_comments_youtube_id", "youtube_comment_id"),
        Index("idx_comments_video_id", "video_id"),
        Index("idx_comments_published_at", "published_at"),
        Index("idx_comments_like_count", "like_count"),
        Index("idx_comments_parent_id", "parent_comment_id"),
        Index("idx_comments_video_published", "video_id", "published_at"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    youtube_comment_id: str = Field(
        max_length=255,
        unique=True,
        index=True,
        nullable=False
    )
    video_id: int = Field(
        foreign_key="videos.id",
        nullable=False,
        index=True,
        sa_column=Column(BigInteger)
    )
    author_channel_id: Optional[str] = Field(default=None, max_length=255)
    author_display_name: Optional[str] = Field(default=None, max_length=255)
    text_original: str = Field(nullable=False)
    like_count: int = Field(default=0)
    published_at: datetime = Field(nullable=False, index=True)
    updated_at_youtube: Optional[datetime] = None
    is_reply: bool = Field(default=False)
    parent_comment_id: Optional[int] = Field(
        default=None,
        foreign_key="comments.id",
        sa_column=Column(BigInteger)
    )

    # Future AI analysis fields
    sentiment_score: Optional[Decimal] = Field(
        default=None,
        max_digits=3,
        decimal_places=2,
        description="Sentiment score from -1.0 (negative) to 1.0 (positive)"
    )
    sentiment_label: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Sentiment label: positive, negative, neutral"
    )
    topic_tags: Optional[list] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Array of detected topics from AI analysis"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
