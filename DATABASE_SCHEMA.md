# Database Schema Design

## Overview
PostgreSQL database optimized for time-series analytics data with efficient storage and querying capabilities.

## Tables

### channels
Stores YouTube channel information.

```sql
CREATE TABLE channels (
    id BIGSERIAL PRIMARY KEY,
    youtube_channel_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    custom_url VARCHAR(255),
    country VARCHAR(10),
    published_at TIMESTAMP WITH TIME ZONE,
    thumbnails JSONB,  -- {default, medium, high}
    is_own_channel BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_channels_youtube_id ON channels(youtube_channel_id);
CREATE INDEX idx_channels_is_own ON channels(is_own_channel);
CREATE INDEX idx_channels_created_at ON channels(created_at);
```

### videos
Stores YouTube video metadata.

```sql
CREATE TABLE videos (
    id BIGSERIAL PRIMARY KEY,
    youtube_video_id VARCHAR(255) UNIQUE NOT NULL,
    channel_id BIGINT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    tags JSONB,  -- array of strings
    category_id VARCHAR(50),
    duration_seconds INTEGER,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50),  -- public, private, unlisted
    thumbnails JSONB,  -- {default, medium, high, standard, maxres}
    definition VARCHAR(10),  -- hd, sd
    dimension VARCHAR(10),  -- 2d, 3d
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_videos_youtube_id ON videos(youtube_video_id);
CREATE INDEX idx_videos_channel_id ON videos(channel_id);
CREATE INDEX idx_videos_published_at ON videos(published_at);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_channel_published ON videos(channel_id, published_at DESC);
```

### video_stats_snapshots
Time-series snapshots of video statistics. Partitioned by month for efficiency.

```sql
CREATE TABLE video_stats_snapshots (
    id BIGSERIAL,
    video_id BIGINT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    view_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    favorite_count BIGINT DEFAULT 0,
    source VARCHAR(50) DEFAULT 'daily_cron',  -- daily_cron, manual, hourly_cron
    PRIMARY KEY (id, captured_at)
) PARTITION BY RANGE (captured_at);

-- Create partitions for current and next months (automated via migration script)
-- Example: CREATE TABLE video_stats_snapshots_2024_01 PARTITION OF video_stats_snapshots
--          FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE INDEX idx_video_stats_video_captured ON video_stats_snapshots(video_id, captured_at DESC);
CREATE INDEX idx_video_stats_captured ON video_stats_snapshots USING BRIN (captured_at);
CREATE INDEX idx_video_stats_view_count ON video_stats_snapshots(view_count);
```

### channel_stats_snapshots
Time-series snapshots of channel statistics. Partitioned by month.

```sql
CREATE TABLE channel_stats_snapshots (
    id BIGSERIAL,
    channel_id BIGINT NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    view_count BIGINT DEFAULT 0,
    subscriber_count BIGINT,  -- NULL if hidden
    video_count INTEGER DEFAULT 0,
    source VARCHAR(50) DEFAULT 'daily_cron',
    PRIMARY KEY (id, captured_at)
) PARTITION BY RANGE (captured_at);

CREATE INDEX idx_channel_stats_channel_captured ON channel_stats_snapshots(channel_id, captured_at DESC);
CREATE INDEX idx_channel_stats_captured ON channel_stats_snapshots USING BRIN (captured_at);
```

### comments
YouTube video comments (selective storage - top comments or recent).

```sql
CREATE TABLE comments (
    id BIGSERIAL PRIMARY KEY,
    youtube_comment_id VARCHAR(255) UNIQUE NOT NULL,
    video_id BIGINT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    author_channel_id VARCHAR(255),
    author_display_name VARCHAR(255),
    text_original TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at_youtube TIMESTAMP WITH TIME ZONE,
    is_reply BOOLEAN DEFAULT FALSE,
    parent_comment_id BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    -- Future AI analysis fields
    sentiment_score DECIMAL(3, 2),  -- -1.0 to 1.0
    sentiment_label VARCHAR(20),  -- positive, negative, neutral
    topic_tags JSONB,  -- array of detected topics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_comments_youtube_id ON comments(youtube_comment_id);
CREATE INDEX idx_comments_video_id ON comments(video_id);
CREATE INDEX idx_comments_published_at ON comments(published_at DESC);
CREATE INDEX idx_comments_like_count ON comments(like_count DESC);
CREATE INDEX idx_comments_parent_id ON comments(parent_comment_id);
CREATE INDEX idx_comments_video_published ON comments(video_id, published_at DESC);
```

### alert_rules
Configurable alert rules.

```sql
CREATE TABLE alert_rules (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100) NOT NULL,  -- video_views_growth, channel_activity_drop, high_engagement, etc.
    params JSONB NOT NULL,  -- Flexible config: {threshold: 10000, period_hours: 24, channel_ids: [1,2]}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alert_rules_type ON alert_rules(type);
CREATE INDEX idx_alert_rules_is_active ON alert_rules(is_active);
```

### alerts
Triggered alerts from alert rules.

```sql
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_rule_id BIGINT NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,  -- video, channel
    entity_id BIGINT NOT NULL,  -- references videos.id or channels.id
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    payload JSONB NOT NULL,  -- Detailed event data: {old_value: 1000, new_value: 15000, delta: 14000}
    status VARCHAR(50) DEFAULT 'new',  -- new, read, archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_rule_id ON alerts(alert_rule_id);
CREATE INDEX idx_alerts_entity ON alerts(entity_type, entity_id);
CREATE INDEX idx_alerts_triggered_at ON alerts(triggered_at DESC);
CREATE INDEX idx_alerts_status ON alerts(status);
```

### notification_targets
Future: External notification endpoints (webhooks, Telegram, etc.).

```sql
CREATE TABLE notification_targets (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- webhook, telegram, slack, email
    config JSONB NOT NULL,  -- {url: "...", token: "...", chat_id: "..."}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_targets_type ON notification_targets(type);
CREATE INDEX idx_notification_targets_is_active ON notification_targets(is_active);
```

### alert_rule_notifications
Many-to-many: which alert rules send to which notification targets.

```sql
CREATE TABLE alert_rule_notifications (
    alert_rule_id BIGINT NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    notification_target_id BIGINT NOT NULL REFERENCES notification_targets(id) ON DELETE CASCADE,
    PRIMARY KEY (alert_rule_id, notification_target_id)
);
```

## Materialized Views for Performance

### mv_video_latest_stats
Latest statistics for each video (refreshed periodically).

```sql
CREATE MATERIALIZED VIEW mv_video_latest_stats AS
SELECT DISTINCT ON (video_id)
    video_id,
    captured_at,
    view_count,
    like_count,
    comment_count,
    favorite_count
FROM video_stats_snapshots
ORDER BY video_id, captured_at DESC;

CREATE UNIQUE INDEX idx_mv_video_latest_stats_video_id ON mv_video_latest_stats(video_id);
```

### mv_channel_latest_stats
Latest statistics for each channel.

```sql
CREATE MATERIALIZED VIEW mv_channel_latest_stats AS
SELECT DISTINCT ON (channel_id)
    channel_id,
    captured_at,
    view_count,
    subscriber_count,
    video_count
FROM channel_stats_snapshots
ORDER BY channel_id, captured_at DESC;

CREATE UNIQUE INDEX idx_mv_channel_latest_stats_channel_id ON mv_channel_latest_stats(channel_id);
```

### mv_video_growth_24h
Video view growth in last 24 hours (refreshed hourly).

```sql
CREATE MATERIALIZED VIEW mv_video_growth_24h AS
WITH latest AS (
    SELECT DISTINCT ON (video_id)
        video_id,
        view_count as current_views,
        captured_at
    FROM video_stats_snapshots
    WHERE captured_at >= NOW() - INTERVAL '48 hours'
    ORDER BY video_id, captured_at DESC
),
day_ago AS (
    SELECT DISTINCT ON (video_id)
        video_id,
        view_count as day_ago_views
    FROM video_stats_snapshots
    WHERE captured_at >= NOW() - INTERVAL '48 hours'
      AND captured_at <= NOW() - INTERVAL '24 hours'
    ORDER BY video_id, captured_at DESC
)
SELECT
    l.video_id,
    l.current_views,
    COALESCE(d.day_ago_views, 0) as day_ago_views,
    (l.current_views - COALESCE(d.day_ago_views, 0)) as views_delta_24h,
    l.captured_at
FROM latest l
LEFT JOIN day_ago d ON l.video_id = d.video_id;

CREATE UNIQUE INDEX idx_mv_video_growth_24h_video_id ON mv_video_growth_24h(video_id);
CREATE INDEX idx_mv_video_growth_24h_delta ON mv_video_growth_24h(views_delta_24h DESC);
```

## Partition Management

Partitions should be created automatically via:
1. Alembic migration script
2. Scheduled task (monthly) to create next month's partitions
3. Retention policy task (optional) to drop old partitions after X years

## Indexing Strategy

1. **B-tree indexes**: Primary keys, foreign keys, frequently filtered columns
2. **BRIN indexes**: Time-series columns (captured_at) - very space-efficient
3. **GIN indexes**: JSONB columns if we need to query inside JSON frequently
4. **Composite indexes**: (entity_id, timestamp) for common access patterns

## Query Optimization Notes

1. **Latest stats**: Use materialized views instead of DISTINCT ON in queries
2. **Time ranges**: Partition pruning automatically filters irrelevant partitions
3. **Aggregations**: Pre-compute common aggregations in materialized views
4. **Growth calculations**: Use window functions or joins between snapshots
5. **Top N queries**: Indexes on metric columns (view_count, like_count) with DESC

## Data Retention Strategy

### Current Phase (MVP)
- Keep all data indefinitely
- Monitor disk usage

### Future Optimization
- Raw snapshots: Keep 90 days at daily granularity
- Aggregated snapshots: Keep 1 year at weekly granularity
- Long-term: Keep monthly aggregations indefinitely
- Implement via partition dropping or archival to cold storage

## Estimated Storage

Assumptions:
- 10 channels, avg 500 videos each = 5,000 videos
- Daily snapshots: 5,000 rows/day
- 1 year: ~1.8M rows in video_stats_snapshots

Storage estimate:
- Each snapshot row: ~100 bytes
- 1.8M rows × 100 bytes = 180 MB/year (very manageable)
- With indexes: ~500 MB/year

Even with 100 channels: ~5 GB/year - totally fine.
