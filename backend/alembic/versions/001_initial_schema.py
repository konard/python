"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-11-03 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create channels table
    op.create_table('channels',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('youtube_channel_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('title', sa.VARCHAR(length=500), nullable=False),
        sa.Column('description', sa.JSON(), nullable=True),
        sa.Column('custom_url', sa.VARCHAR(length=255), nullable=True),
        sa.Column('country', sa.VARCHAR(length=10), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('thumbnails', sa.JSON(), nullable=True),
        sa.Column('is_own_channel', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('youtube_channel_id')
    )
    op.create_index('idx_channels_youtube_id', 'channels', ['youtube_channel_id'])
    op.create_index('idx_channels_is_own', 'channels', ['is_own_channel'])
    op.create_index('idx_channels_created_at', 'channels', ['created_at'])

    # Create videos table
    op.create_table('videos',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('youtube_video_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.VARCHAR(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('category_id', sa.VARCHAR(length=50), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.VARCHAR(length=50), nullable=True),
        sa.Column('thumbnails', sa.JSON(), nullable=True),
        sa.Column('definition', sa.VARCHAR(length=10), nullable=True),
        sa.Column('dimension', sa.VARCHAR(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('youtube_video_id')
    )
    op.create_index('idx_videos_youtube_id', 'videos', ['youtube_video_id'])
    op.create_index('idx_videos_channel_id', 'videos', ['channel_id'])
    op.create_index('idx_videos_published_at', 'videos', ['published_at'])
    op.create_index('idx_videos_status', 'videos', ['status'])
    op.create_index('idx_videos_channel_published', 'videos', ['channel_id', 'published_at'])

    # Create channel_stats_snapshots table (partitioned)
    op.create_table('channel_stats_snapshots',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('view_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('subscriber_count', sa.BigInteger(), nullable=True),
        sa.Column('video_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('source', sa.VARCHAR(length=50), nullable=False, server_default='daily_cron'),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_channel_stats_channel_captured', 'channel_stats_snapshots', ['channel_id', 'captured_at'])

    # Create video_stats_snapshots table (partitioned)
    op.create_table('video_stats_snapshots',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('video_id', sa.BigInteger(), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('view_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('like_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('comment_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('favorite_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('source', sa.VARCHAR(length=50), nullable=False, server_default='daily_cron'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_video_stats_video_captured', 'video_stats_snapshots', ['video_id', 'captured_at'])
    op.create_index('idx_video_stats_view_count', 'video_stats_snapshots', ['view_count'])

    # Create comments table
    op.create_table('comments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('youtube_comment_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('video_id', sa.BigInteger(), nullable=False),
        sa.Column('author_channel_id', sa.VARCHAR(length=255), nullable=True),
        sa.Column('author_display_name', sa.VARCHAR(length=255), nullable=True),
        sa.Column('text_original', sa.Text(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at_youtube', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_reply', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_comment_id', sa.BigInteger(), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('sentiment_label', sa.VARCHAR(length=20), nullable=True),
        sa.Column('topic_tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('youtube_comment_id')
    )
    op.create_index('idx_comments_youtube_id', 'comments', ['youtube_comment_id'])
    op.create_index('idx_comments_video_id', 'comments', ['video_id'])
    op.create_index('idx_comments_published_at', 'comments', ['published_at'])
    op.create_index('idx_comments_like_count', 'comments', ['like_count'])
    op.create_index('idx_comments_parent_id', 'comments', ['parent_comment_id'])
    op.create_index('idx_comments_video_published', 'comments', ['video_id', 'published_at'])

    # Create alert_rules table
    op.create_table('alert_rules',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.VARCHAR(length=100), nullable=False),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_rules_type', 'alert_rules', ['type'])
    op.create_index('idx_alert_rules_is_active', 'alert_rules', ['is_active'])

    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('alert_rule_id', sa.BigInteger(), nullable=False),
        sa.Column('entity_type', sa.VARCHAR(length=50), nullable=False),
        sa.Column('entity_id', sa.BigInteger(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.VARCHAR(length=50), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['alert_rule_id'], ['alert_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alerts_rule_id', 'alerts', ['alert_rule_id'])
    op.create_index('idx_alerts_entity', 'alerts', ['entity_type', 'entity_id'])
    op.create_index('idx_alerts_triggered_at', 'alerts', ['triggered_at'])
    op.create_index('idx_alerts_status', 'alerts', ['status'])

    # Create notification_targets table
    op.create_table('notification_targets',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('type', sa.VARCHAR(length=50), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notification_targets_type', 'notification_targets', ['type'])
    op.create_index('idx_notification_targets_is_active', 'notification_targets', ['is_active'])

    # Create alert_rule_notifications table
    op.create_table('alert_rule_notifications',
        sa.Column('alert_rule_id', sa.BigInteger(), nullable=False),
        sa.Column('notification_target_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['alert_rule_id'], ['alert_rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['notification_target_id'], ['notification_targets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('alert_rule_id', 'notification_target_id')
    )


def downgrade() -> None:
    op.drop_table('alert_rule_notifications')
    op.drop_table('notification_targets')
    op.drop_table('alerts')
    op.drop_table('alert_rules')
    op.drop_table('comments')
    op.drop_table('video_stats_snapshots')
    op.drop_table('channel_stats_snapshots')
    op.drop_table('videos')
    op.drop_table('channels')
