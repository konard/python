# Technology Stack and Architecture Decision

## Backend Stack

### Core Framework: FastAPI 0.115.0+
**Justification:**
- Modern async support for efficient API handling
- Automatic OpenAPI documentation generation
- Excellent performance (comparable to Node.js/Go)
- Native Pydantic integration for data validation
- Well-suited for API-first architecture
- Easier to integrate with background tasks than Django

### Python Version: 3.11+
**Justification:**
- Performance improvements over 3.10
- Better error messages
- Modern typing features
- Wide ecosystem support

### ORM: SQLModel (SQLAlchemy 2.0 based)
**Justification:**
- Combines SQLAlchemy and Pydantic models
- Type safety with Python type hints
- Seamless integration with FastAPI
- Modern async support
- Less boilerplate than pure SQLAlchemy

### Database: PostgreSQL 15+
**Justification:**
- Excellent JSONB support for flexible data (tags, thumbnails)
- Robust partitioning for time-series data (snapshots)
- Powerful indexing (GIN, BRIN for timestamps)
- Materialized views for aggregations
- Proven scalability for analytics workloads

### Task Queue: Celery 5.3+ with Redis
**Justification:**
- Industry standard for Python background tasks
- Flexible scheduling (cron-like patterns)
- Task prioritization and retry logic
- Monitoring tools (Flower)
- Redis as broker/backend: fast, lightweight

### Caching: Redis 7+
**Justification:**
- Cache YouTube API responses
- Rate limiting implementation
- Session storage (future OAuth)
- Fast key-value operations

## Frontend Stack

### Framework: Next.js 14+ (React)
**Justification:**
- Server-side rendering for better SEO
- File-based routing
- API routes for BFF pattern
- Excellent TypeScript support
- Optimized production builds
- Image optimization out of the box

### Language: TypeScript 5+
**Justification:**
- Type safety catches bugs early
- Better IDE support
- Self-documenting code
- Industry standard for modern React

### UI Library: Tailwind CSS + Shadcn/ui
**Justification:**
- Tailwind: Utility-first, highly customizable, small bundle
- Shadcn/ui: Modern, accessible components, full control
- Dark mode support out of the box
- Professional analytics dashboard aesthetic

### Charts: Recharts
**Justification:**
- Built on D3.js, powerful and flexible
- React-native components
- Good documentation
- Covers all needed chart types (line, bar, area)

## DevOps & Infrastructure

### Containerization: Docker + Docker Compose
**Justification:**
- Consistent development environment
- Easy deployment
- Service isolation
- Version control for infrastructure

### CI/CD: GitHub Actions
**Justification:**
- Native GitHub integration
- Free for public repos
- Flexible workflow definitions
- Good ecosystem of actions

### Migrations: Alembic
**Justification:**
- Standard for SQLAlchemy
- Automatic migration generation
- Version control for schema
- Supports complex migrations

## Architecture Modules

```
youtube-analytics/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── models/           # SQLModel ORM models
│   │   ├── services/
│   │   │   ├── data_ingestion/    # YouTube API client
│   │   │   ├── analytics/         # Metrics calculation
│   │   │   ├── alerts/            # Alert rules & triggers
│   │   │   └── future_ai/         # AI interfaces (stubs)
│   │   ├── tasks/            # Celery tasks
│   │   ├── core/             # Config, dependencies
│   │   └── utils/            # Helpers
│   ├── alembic/              # Migrations
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app directory
│   │   ├── components/       # React components
│   │   ├── lib/              # Utils, API client
│   │   └── types/            # TypeScript types
│   └── public/
├── docker/                   # Docker configs
├── .github/workflows/        # CI/CD
└── docs/                     # Documentation
```

## Data Storage Strategy

### Time-Series Optimization
1. **Partitioning:** Partition snapshots tables by month
2. **Indexing:** B-tree on (video_id, captured_at), BRIN on captured_at
3. **Aggregation:** Materialized views for common queries
4. **Retention:** Raw snapshots kept indefinitely, but can add retention policy later

### API Rate Limiting Strategy
- YouTube Data API quota: 10,000 units/day (default)
- Video list: 1 unit, video details: 1 unit per video
- Channel details: 1 unit
- Strategy:
  - Cache responses (TTL: 1 hour for static data, 6 hours for snapshots)
  - Batch requests (50 videos per request)
  - Prioritize active channels (updated daily)
  - Older content (7+ days): weekly updates
  - User can manually trigger updates (with cooldown)

## Future Extensibility

### OAuth Integration (Phase 2)
- YouTube Analytics API for own channels
- Deeper insights (traffic sources, demographics)
- Already designed: channels.is_own_channel flag

### AI Integration (Phase 3)
- Modular design with interfaces
- Comment sentiment analysis
- Content idea generation
- Script generation
- Ready for OpenAI, Anthropic, or local LLMs

### Notification Channels (Phase 4)
- Webhook system already designed
- Easy to add: Telegram, Slack, Discord
- notifications_targets table ready

## Environment Variables

Required:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `SECRET_KEY`: Application secret

Optional:
- `CELERY_BROKER_URL`: Override Redis URL for Celery
- `ENVIRONMENT`: dev/staging/prod
- `LOG_LEVEL`: Logging verbosity
