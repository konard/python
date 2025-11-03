# YouTube Analytics System

A comprehensive YouTube channel analytics platform for tracking channel performance, video metrics, and competitive analysis using YouTube Data API v3.

## Features

- **Multi-Channel Tracking**: Monitor your own channels and competitors (public data only)
- **Time-Series Analytics**: Daily snapshots of channel and video statistics
- **Trend Detection**: Identify trending videos and growth patterns
- **Alert System**: Configurable alerts for significant events (view spikes, engagement drops)
- **Modern Dashboard**: React-based UI with interactive charts and reports
- **Efficient Data Storage**: PostgreSQL with partitioning for time-series data
- **Background Processing**: Celery-based task queue for periodic updates
- **API-First Design**: RESTful API with FastAPI

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern async web framework
- **SQLModel** - ORM with SQLAlchemy 2.0 and Pydantic
- **PostgreSQL 15+** - Primary database
- **Redis 7+** - Caching and task queue
- **Celery** - Background task processing
- **Alembic** - Database migrations

### Frontend
- **Next.js 14+** - React framework with SSR
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS + Shadcn/ui** - Modern UI components
- **Recharts** - Data visualization

## Project Structure

```
youtube-analytics/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── models/          # SQLModel ORM models
│   │   ├── services/
│   │   │   ├── data_ingestion/  # YouTube API client
│   │   │   ├── analytics/       # Metrics calculation
│   │   │   ├── alerts/          # Alert rules & triggers
│   │   │   └── future_ai/       # AI interfaces (planned)
│   │   ├── tasks/           # Celery tasks
│   │   ├── core/            # Config, database
│   │   └── utils/           # Helper functions
│   ├── alembic/             # Database migrations
│   ├── tests/               # Unit & integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app directory
│   │   ├── components/      # React components
│   │   ├── lib/             # Utils, API client
│   │   └── types/           # TypeScript types
│   └── package.json
├── docker/                  # Docker configurations
├── .github/workflows/       # CI/CD pipelines
└── docs/                    # Documentation
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)
- YouTube Data API v3 key ([Get one here](https://console.cloud.google.com/apis/credentials))

### 1. Clone Repository

```bash
git clone <repository-url>
cd youtube-analytics
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env with your configuration
```

### 3. Configure Environment Variables

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/youtube_analytics

# Redis
REDIS_URL=redis://localhost:6379/0

# YouTube API
YOUTUBE_API_KEY=your-youtube-api-key-here

# Secret key (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-secret-key-here
```

### 4. Database Setup

```bash
# Create database
createdb youtube_analytics

# Run migrations
cd backend
alembic upgrade head
```

### 5. Run Backend

```bash
# Terminal 1: FastAPI server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
cd backend
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
cd backend
celery -A app.tasks.celery_app beat --loglevel=info
```

### 6. Frontend Setup (Coming Soon)

```bash
cd frontend
npm install
npm run dev
```

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Usage

### Adding Channels

1. Navigate to the dashboard
2. Enter YouTube channel URL in any format:
   - `https://www.youtube.com/@mkbhd`
   - `https://www.youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ`
   - `https://www.youtube.com/c/MarquesBrownlee`
3. Mark as "Own Channel" if it's yours

### API Endpoints

- `POST /api/v1/channels` - Add new channel
- `GET /api/v1/channels` - List all channels
- `GET /api/v1/channels/{id}` - Get channel details
- `GET /api/v1/channels/{id}/videos` - Get channel videos
- `GET /api/v1/videos/{id}` - Get video details
- `GET /api/v1/trending/videos` - Get trending videos
- `GET /api/v1/analytics/compare` - Compare channels

Full API documentation: http://localhost:8000/docs

## Development

### Running Tests

```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type checking
mypy app/
```

### Creating Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Architecture

### Data Collection Strategy

1. **Initial Import**: When adding a channel, fetch all videos and create initial snapshots
2. **Daily Updates**: Celery task updates stats for all channels/videos daily at 2 AM UTC
3. **Caching**: Redis caches API responses (1-6 hour TTL) to minimize quota usage
4. **Rate Limiting**: Respects YouTube API quota (10,000 units/day default)

### Database Design

- **Partitioned Tables**: Snapshots partitioned by month for efficient queries
- **Materialized Views**: Pre-computed aggregations for common queries
- **Indexes**: Optimized for time-range queries and filtering

### API Quota Management

YouTube Data API quota: 10,000 units/day (default)

Costs:
- Channel details: 1 unit
- Video list: 1 unit
- Video details: 1 unit per batch (up to 50 videos)

Strategy:
- Batch video requests (50 per call)
- Cache responses aggressively
- Prioritize active content (recent videos updated more frequently)
- Older videos (7+ days): weekly updates

## Future Enhancements

### Phase 2: YouTube Analytics API (Planned)
- OAuth integration for own channels
- Detailed analytics (traffic sources, demographics)
- Revenue data (for monetized channels)

### Phase 3: AI Integration (Planned)
- Comment sentiment analysis
- Content idea generation
- Automated script writing
- Trend prediction

### Phase 4: Notifications (Planned)
- Webhook support
- Telegram/Slack/Discord notifications
- Email alerts
- Custom notification rules

## License

MIT License

## Support

For issues and questions, create an issue in GitHub.