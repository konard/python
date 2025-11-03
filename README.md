# YouTube Analytics System

A comprehensive analytics platform for tracking and analyzing YouTube channels and videos, specifically designed for the health niche. Monitor your own channels and competitors, track growth trends, analyze engagement, and receive alerts on significant changes.

## 🎯 Features

### Core Functionality
- **Channel Management**: Add and track multiple YouTube channels (own and competitors)
- **Automated Data Collection**: Regular snapshots of channel and video statistics
- **Historical Tracking**: Store and analyze performance data over time
- **YouTube Data API v3 Integration**: Fetch public data for any channel
- **Rate Limiting & Caching**: Smart API usage to stay within quotas

### Analytics & Insights
- **Performance Metrics**: Views, likes, comments, engagement rates
- **Growth Analysis**: Track subscriber and view count changes
- **Trending Videos**: Identify fast-growing content
- **Channel Comparison**: Compare performance across multiple channels
- **Custom Time Periods**: Analyze data for any date range

### Alerts & Notifications
- **Custom Alert Rules**: Set thresholds for important events
- **Real-time Monitoring**: Get notified when videos or channels cross thresholds
- **Configurable Triggers**: Views growth, engagement drops, new videos

### Future AI Features (Stub Interfaces Ready)
- **Sentiment Analysis**: Analyze comment sentiment and tone
- **Topic Extraction**: Identify trending topics in comments
- **Content Ideas**: Generate video ideas based on performance data
- **Script Generation**: AI-assisted video script creation

## 🏗️ Architecture

### Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy 2.0 (async ORM)
- PostgreSQL (database)
- Redis (caching & task queue)
- Celery (background tasks)
- Alembic (migrations)

**Frontend:**
- Next.js 14+ (React framework)
- TypeScript
- Tailwind CSS + shadcn/ui
- Recharts (data visualization)

**Infrastructure:**
- Docker & Docker Compose
- GitHub Actions (CI/CD)

### System Components

```
backend/
├── app/
│   ├── data_ingestion/    # YouTube API client, rate limiting, caching
│   ├── storage/           # Database models, repositories
│   ├── analytics/         # Metrics calculation
│   ├── alerts/            # Alert rules and triggers
│   ├── tasks/             # Celery background tasks
│   ├── api/               # FastAPI REST endpoints
│   ├── future_ai/         # AI integration interfaces (stubs)
│   └── utils/             # Utilities
├── alembic/               # Database migrations
└── tests/                 # Test suite

frontend/
├── src/
│   ├── app/               # Next.js app router (pages)
│   ├── components/        # React components
│   ├── lib/               # Utilities & API client
│   └── hooks/             # Custom React hooks
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- YouTube Data API v3 key ([Get one here](https://console.cloud.google.com/apis/credentials))

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/mastint777/python.git
cd python
```

2. **Configure environment variables**
```bash
# Copy the example env file
cp backend/.env.example backend/.env

# Edit backend/.env and add your YouTube API key
# YOUTUBE_API_KEY=your_api_key_here
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Celery Worker
- Celery Beat (scheduler)
- Frontend (port 3000)

4. **Run database migrations**
```bash
docker-compose exec backend alembic upgrade head
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📖 Usage

### Adding a Channel

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/channels \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/@examplechannel",
    "is_own_channel": false
  }'
```

Supported URL formats:
- `https://www.youtube.com/@username`
- `https://www.youtube.com/channel/UC...`
- `https://www.youtube.com/user/username`
- `https://www.youtube.com/c/customname`
- Video URLs (extracts channel automatically)

### API Endpoints

**Channels:**
- `POST /api/v1/channels` - Add new channel
- `GET /api/v1/channels` - List all channels
- `GET /api/v1/channels/{id}` - Get channel details
- `PUT /api/v1/channels/{id}` - Update channel
- `DELETE /api/v1/channels/{id}` - Remove channel
- `POST /api/v1/channels/{id}/refresh` - Manual refresh

**Videos:**
- `GET /api/v1/videos` - List videos
- `GET /api/v1/videos/{id}` - Get video details
- `GET /api/v1/videos/{id}/stats` - Get statistics timeline

**Analytics:**
- `GET /api/v1/analytics/trending` - Get trending videos
- `GET /api/v1/analytics/compare` - Compare channels
- `GET /api/v1/analytics/metrics` - Aggregated metrics

**Alerts:**
- `GET /api/v1/alerts` - List triggered alerts
- `GET /api/v1/alerts/rules` - List alert rules
- `POST /api/v1/alerts/rules` - Create alert rule

Full API documentation: http://localhost:8000/docs

## 🔧 Development

### Local Development (without Docker)

1. **Install Python dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set up PostgreSQL and Redis**
```bash
# Install PostgreSQL and Redis locally or use Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16
docker run -d -p 6379:6379 redis:7-alpine
```

3. **Run migrations**
```bash
cd backend
alembic upgrade head
```

4. **Start the backend**
```bash
cd backend
uvicorn app.main:app --reload
```

5. **Start Celery worker (in another terminal)**
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

6. **Start Celery beat (in another terminal)**
```bash
cd backend
celery -A app.tasks.celery_app beat --loglevel=info
```

### Code Quality

**Linting:**
```bash
cd backend
ruff check .
```

**Formatting:**
```bash
cd backend
black .
```

**Type checking:**
```bash
cd backend
mypy .
```

**Run tests:**
```bash
cd backend
pytest
```

## 📊 Database Schema

### Key Tables

- **channels**: YouTube channel information
- **videos**: Video metadata
- **channel_stats_snapshots**: Historical channel statistics
- **video_stats_snapshots**: Historical video statistics
- **comments**: Video comments (for future AI analysis)
- **alert_rules**: Alert rule configurations
- **alerts**: Triggered alerts
- **notification_targets**: Future webhook/notification configs

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed schema documentation.

## ⚙️ Configuration

### Environment Variables

Key configuration options (see `backend/.env.example`):

**YouTube API:**
- `YOUTUBE_API_KEY`: Your YouTube Data API v3 key
- `YOUTUBE_API_QUOTA_LIMIT`: Daily quota limit (default: 10000)
- `YOUTUBE_API_REQUESTS_PER_SECOND`: Rate limit (default: 100)

**Database:**
- `POSTGRES_SERVER`: PostgreSQL host
- `POSTGRES_PORT`: PostgreSQL port
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DB`: Database name

**Cache TTL:**
- `CACHE_TTL_CHANNEL_DETAILS`: Channel info cache (default: 3600s)
- `CACHE_TTL_VIDEO_STATS`: Video stats cache (default: 1800s)

**Task Schedule:**
- `UPDATE_STATS_CRON_HOUR`: Hour to run daily updates (0-23)
- `CHECK_ALERTS_INTERVAL_MINUTES`: Alert check frequency

## 🎨 Frontend

The frontend is built with Next.js 14 and provides:

- **Dashboard**: Overview of all channels
- **Channel Pages**: Detailed channel analytics
- **Video Pages**: Video performance over time
- **Trending**: Fast-growing content
- **Alerts**: Alert management interface
- **Comparison**: Side-by-side channel comparison

Frontend setup:
```bash
cd frontend
npm install
npm run dev
```

## 🤖 Future AI Features

The system includes abstract interfaces for future AI integrations:

- `CommentAnalyzer`: Sentiment analysis and topic extraction
- `ContentIdeaGenerator`: AI-powered content suggestions
- `ScriptGenerator`: Video script generation

These are currently stub implementations. To integrate real AI:

1. Implement the interfaces in `backend/app/future_ai/interfaces.py`
2. Configure AI API keys in environment variables
3. Enable features with `ENABLE_AI_FEATURES=true`

## 📈 Performance & Optimization

### Rate Limiting
- Redis-based quota tracking
- Automatic retry with exponential backoff
- Daily quota management with reset tracking

### Caching Strategy
- Channel details: 1 hour TTL
- Video statistics: 30 minutes TTL
- Batch requests for efficiency (up to 50 items)

### Database Optimization
- Indexes on frequently queried fields
- Partitioning strategy for snapshot tables
- Efficient pagination for large datasets

## 🧪 Testing

Run the test suite:
```bash
cd backend
pytest tests/ -v --cov=app
```

## 📝 Contributing

This project follows standard Python conventions:

1. Use Black for code formatting
2. Use Ruff for linting
3. Write tests for new features
4. Update documentation

## 📜 License

[Add your license here]

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Uses [YouTube Data API v3](https://developers.google.com/youtube/v3)
- Frontend powered by [Next.js](https://nextjs.org/)

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/mastint777/python/issues
- Documentation: See [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Note**: This system uses only public YouTube Data API v3. For enhanced analytics on your own channels, consider integrating YouTube Analytics API with OAuth in the future.
