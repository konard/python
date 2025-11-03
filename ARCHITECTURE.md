# YouTube Analytics System - Architecture

## Technology Stack

### Backend
- **Python**: 3.11+ (modern features, good performance)
- **FastAPI**: Modern async web framework, automatic API docs, excellent performance
- **SQLAlchemy 2.0**: ORM with async support
- **Alembic**: Database migrations
- **PostgreSQL**: Robust relational database with JSONB support
- **Redis**: Caching and Celery broker
- **Celery**: Background task processing
- **Pydantic**: Data validation and serialization

### Frontend
- **Next.js 14+**: React framework with SSR/SSG support
- **TypeScript**: Type safety
- **Tailwind CSS + shadcn/ui**: Modern UI components
- **Recharts**: Data visualization
- **React Query**: Server state management
- **Zustand**: Client state management

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **GitHub Actions**: CI/CD pipeline
- **pytest**: Testing framework
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **mypy**: Static type checking

## System Architecture

### Module Structure

```
youtube-analytics/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration management
│   │   ├── dependencies.py         # Dependency injection
│   │   │
│   │   ├── data_ingestion/         # YouTube API integration
│   │   │   ├── __init__.py
│   │   │   ├── youtube_client.py   # YouTube Data API v3 client
│   │   │   ├── channel_parser.py   # Parse channel URLs
│   │   │   ├── rate_limiter.py     # API rate limiting
│   │   │   └── cache.py            # Redis caching layer
│   │   │
│   │   ├── storage/                # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # DB connection and session
│   │   │   ├── models.py           # SQLAlchemy ORM models
│   │   │   ├── repositories/       # Repository pattern
│   │   │   │   ├── __init__.py
│   │   │   │   ├── channel.py
│   │   │   │   ├── video.py
│   │   │   │   ├── snapshot.py
│   │   │   │   └── alert.py
│   │   │   └── schemas.py          # Pydantic schemas
│   │   │
│   │   ├── analytics/              # Metrics calculation
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py          # Core metrics calculations
│   │   │   ├── aggregations.py     # Data aggregation
│   │   │   ├── trends.py           # Trend analysis
│   │   │   └── comparisons.py      # Channel comparisons
│   │   │
│   │   ├── alerts/                 # Alert system
│   │   │   ├── __init__.py
│   │   │   ├── rules.py            # Alert rule definitions
│   │   │   ├── triggers.py         # Rule evaluation
│   │   │   └── notifications.py    # Notification handling
│   │   │
│   │   ├── tasks/                  # Celery tasks
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py       # Celery configuration
│   │   │   ├── import_tasks.py     # Channel/video import
│   │   │   ├── update_tasks.py     # Periodic updates
│   │   │   └── alert_tasks.py      # Alert checking
│   │   │
│   │   ├── api/                    # REST API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── channels.py
│   │   │   │   ├── videos.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── alerts.py
│   │   │   │   └── trending.py
│   │   │   └── deps.py
│   │   │
│   │   ├── future_ai/              # AI integration stubs
│   │   │   ├── __init__.py
│   │   │   ├── interfaces.py       # Abstract interfaces
│   │   │   ├── comment_analysis.py # Sentiment analysis stub
│   │   │   ├── content_ideas.py    # Idea generation stub
│   │   │   └── script_generator.py # Script generation stub
│   │   │
│   │   └── utils/                  # Utilities
│   │       ├── __init__.py
│   │       ├── logging.py
│   │       └── datetime_helpers.py
│   │
│   ├── alembic/                    # Database migrations
│   ├── tests/                      # Test suite
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js app router
│   │   │   ├── page.tsx            # Dashboard home
│   │   │   ├── channels/
│   │   │   ├── videos/
│   │   │   ├── trending/
│   │   │   ├── alerts/
│   │   │   └── compare/
│   │   │
│   │   ├── components/             # React components
│   │   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── charts/             # Chart components
│   │   │   ├── channel/            # Channel components
│   │   │   └── video/              # Video components
│   │   │
│   │   ├── lib/                    # Utilities
│   │   │   ├── api.ts              # API client
│   │   │   └── utils.ts
│   │   │
│   │   ├── hooks/                  # Custom React hooks
│   │   └── types/                  # TypeScript types
│   │
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
│
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
└── README.md
```

## Database Schema

### Core Tables

#### channels
```sql
- id: SERIAL PRIMARY KEY
- youtube_channel_id: VARCHAR(255) UNIQUE NOT NULL
- title: VARCHAR(500)
- description: TEXT
- custom_url: VARCHAR(255)
- country: VARCHAR(10)
- thumbnails: JSONB
- is_own_channel: BOOLEAN DEFAULT false
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### videos
```sql
- id: SERIAL PRIMARY KEY
- youtube_video_id: VARCHAR(255) UNIQUE NOT NULL
- channel_id: INTEGER FK(channels.id) ON DELETE CASCADE
- title: VARCHAR(500)
- description: TEXT
- tags: JSONB
- category_id: VARCHAR(50)
- duration_seconds: INTEGER
- published_at: TIMESTAMP
- status: VARCHAR(50)
- thumbnails: JSONB
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
- INDEX: (channel_id, published_at)
- INDEX: (published_at)
```

#### channel_stats_snapshots
```sql
- id: SERIAL PRIMARY KEY
- channel_id: INTEGER FK(channels.id) ON DELETE CASCADE
- captured_at: TIMESTAMP NOT NULL
- view_count: BIGINT
- subscriber_count: BIGINT
- hidden_subscriber_count: BOOLEAN
- video_count: INTEGER
- created_at: TIMESTAMP DEFAULT NOW()
- INDEX: (channel_id, captured_at DESC)
- UNIQUE: (channel_id, captured_at)
```

#### video_stats_snapshots
```sql
- id: SERIAL PRIMARY KEY
- video_id: INTEGER FK(videos.id) ON DELETE CASCADE
- captured_at: TIMESTAMP NOT NULL
- view_count: BIGINT
- like_count: INTEGER
- comment_count: INTEGER
- favorite_count: INTEGER
- created_at: TIMESTAMP DEFAULT NOW()
- INDEX: (video_id, captured_at DESC)
- UNIQUE: (video_id, captured_at)
```

#### comments (optional, for future AI analysis)
```sql
- id: SERIAL PRIMARY KEY
- youtube_comment_id: VARCHAR(255) UNIQUE NOT NULL
- video_id: INTEGER FK(videos.id) ON DELETE CASCADE
- author_channel_id: VARCHAR(255)
- text_original: TEXT
- like_count: INTEGER
- published_at: TIMESTAMP
- sentiment_score: FLOAT  # Future AI field
- topic_tags: JSONB       # Future AI field
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
- INDEX: (video_id, published_at DESC)
```

#### alert_rules
```sql
- id: SERIAL PRIMARY KEY
- name: VARCHAR(255)
- type: VARCHAR(100) NOT NULL  # 'video_views_growth', 'channel_activity_drop', etc.
- params: JSONB NOT NULL
- is_active: BOOLEAN DEFAULT true
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### alerts
```sql
- id: SERIAL PRIMARY KEY
- alert_rule_id: INTEGER FK(alert_rules.id) ON DELETE CASCADE
- entity_type: VARCHAR(50)  # 'video' or 'channel'
- entity_id: INTEGER
- triggered_at: TIMESTAMP NOT NULL
- payload: JSONB
- status: VARCHAR(50) DEFAULT 'new'  # 'new', 'read', 'dismissed'
- created_at: TIMESTAMP DEFAULT NOW()
- INDEX: (status, triggered_at DESC)
- INDEX: (entity_type, entity_id)
```

#### notification_targets (future)
```sql
- id: SERIAL PRIMARY KEY
- type: VARCHAR(50)  # 'internal', 'webhook', 'telegram', etc.
- config: JSONB
- is_active: BOOLEAN DEFAULT true
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

## Data Flow

### 1. Channel Import Flow
```
User enters channel URL
    ↓
Parse URL → Extract channel_id
    ↓
Store channel in DB
    ↓
Trigger Celery task: import_channel_videos
    ↓
YouTube API: Fetch channel details + all videos
    ↓
Store videos in DB
    ↓
Create initial snapshots
    ↓
Return success
```

### 2. Periodic Update Flow (Daily Cron)
```
Celery Beat triggers update_all_channels
    ↓
For each channel:
    ↓
    Fetch channel statistics → Store snapshot
    ↓
    Fetch all videos (paginated)
        ↓
        For each video: Fetch statistics → Store snapshot
    ↓
Calculate metrics & check alerts
```

### 3. Analytics Request Flow
```
User requests analytics (via API)
    ↓
API receives request with filters (channel_id, date_range)
    ↓
Repository queries snapshots
    ↓
Analytics service calculates metrics:
    - Growth rates
    - Engagement rates
    - Trends
    ↓
Cache results in Redis (if applicable)
    ↓
Return JSON response
```

### 4. Alert Flow
```
Periodic task: check_alerts
    ↓
For each active alert rule:
    ↓
    Query relevant data (snapshots, metrics)
    ↓
    Evaluate rule conditions
    ↓
    If triggered:
        Create alert record
        Mark status as 'new'
        (Future: Send notifications)
```

## API Endpoints

### Channels
- `POST /api/v1/channels` - Add new channel by URL
- `GET /api/v1/channels` - List all channels (with filters)
- `GET /api/v1/channels/{id}` - Get channel details
- `PUT /api/v1/channels/{id}` - Update channel settings
- `DELETE /api/v1/channels/{id}` - Remove channel
- `GET /api/v1/channels/{id}/videos` - List channel videos
- `GET /api/v1/channels/{id}/stats` - Get channel statistics
- `POST /api/v1/channels/{id}/refresh` - Trigger manual refresh

### Videos
- `GET /api/v1/videos` - List videos (with filters)
- `GET /api/v1/videos/{id}` - Get video details
- `GET /api/v1/videos/{id}/stats` - Get video statistics over time
- `GET /api/v1/videos/{id}/comments` - Get video comments

### Analytics
- `GET /api/v1/analytics/trending` - Get trending videos
- `GET /api/v1/analytics/compare` - Compare channels
- `GET /api/v1/analytics/metrics` - Get aggregated metrics

### Alerts
- `GET /api/v1/alerts` - List alerts
- `GET /api/v1/alerts/{id}` - Get alert details
- `PUT /api/v1/alerts/{id}` - Update alert status
- `GET /api/v1/alert-rules` - List alert rules
- `POST /api/v1/alert-rules` - Create alert rule
- `PUT /api/v1/alert-rules/{id}` - Update alert rule
- `DELETE /api/v1/alert-rules/{id}` - Delete alert rule

## Rate Limiting Strategy

YouTube Data API v3 quotas:
- Default: 10,000 units/day
- Cost per operation:
  - channels.list: 1 unit
  - videos.list: 1 unit
  - playlistItems.list: 1 unit
  - commentThreads.list: 1 unit

### Strategy:
1. **Redis-based rate limiter** - Track daily quota usage
2. **Batch requests** - Use `id` parameter to fetch up to 50 items
3. **Smart caching** - Cache responses for 1-24 hours based on data age
4. **Prioritization** - Recent videos updated more frequently
5. **Exponential backoff** - For rate limit errors

## Optimization Strategies

### Database
1. **Partitioning** - Partition snapshots by month
2. **Indexes** - Strategic indexes on (entity_id, captured_at)
3. **Materialized views** - Pre-calculated aggregations
4. **Archival** - Move old snapshots to archive tables

### Caching
1. **Response cache** - Cache API responses (5-60 min TTL)
2. **Query cache** - Cache complex queries
3. **CDN** - Static assets and thumbnails

### Background Tasks
1. **Priority queues** - Separate queues for import vs. updates
2. **Task deduplication** - Prevent duplicate tasks
3. **Graceful degradation** - Continue on partial failures

## Future AI Integration

### Interfaces (Stubs)

```python
# app/future_ai/interfaces.py

class CommentAnalyzer(ABC):
    @abstractmethod
    async def analyze_sentiment(self, comments: List[Comment]) -> SentimentResult:
        """Analyze sentiment of comments"""
        pass

    @abstractmethod
    async def extract_topics(self, comments: List[Comment]) -> List[Topic]:
        """Extract main topics from comments"""
        pass

class ContentIdeaGenerator(ABC):
    @abstractmethod
    async def generate_ideas(self, channel_stats: ChannelStats) -> List[ContentIdea]:
        """Generate content ideas based on channel performance"""
        pass

class ScriptGenerator(ABC):
    @abstractmethod
    async def generate_script(self, topic: str, parameters: dict) -> VideoScript:
        """Generate video script for given topic"""
        pass
```

## Security Considerations

1. **Environment variables** - All secrets in .env
2. **Input validation** - Pydantic schemas for all inputs
3. **SQL injection** - ORM prevents injection
4. **Rate limiting** - API rate limiting (per IP/user)
5. **CORS** - Proper CORS configuration
6. **Secrets management** - Use Docker secrets in production

## Monitoring & Logging

1. **Structured logging** - JSON logs with context
2. **Error tracking** - Capture and log all errors
3. **Metrics** - Track API latency, task durations
4. **Health checks** - `/health` endpoint for monitoring

## Deployment

### Development
```bash
docker-compose up
```

### Production (Future)
- Container orchestration (Kubernetes/ECS)
- Load balancing
- Database replicas
- Redis cluster
- Horizontal scaling of Celery workers
