# YouTube Analytics System for Health Channels

A comprehensive YouTube channel analytics platform for tracking channel performance, video metrics, and competitive analysis using YouTube Data API v3.

## 🎯 Features

- **Multi-Channel Tracking**: Monitor your own channels and competitors (public data only)
- **Multiple API Keys Support**: Intelligent rotation across multiple YouTube API keys with quota tracking
- **Time-Series Analytics**: Daily snapshots of channel and video statistics
- **Trend Detection**: Identify trending videos and growth patterns
- **Modern Dashboard**: React-based UI with interactive views
- **Efficient Data Storage**: SQLite for MVP (easily upgradable to PostgreSQL)
- **Background Scheduling**: APScheduler for periodic updates
- **API-First Design**: RESTful API with FastAPI

## 📋 Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern async web framework
- **SQLModel** - ORM with SQLAlchemy 2.0 and Pydantic
- **SQLite** - Database (MVP - PostgreSQL-ready)
- **APScheduler** - Background task scheduling
- **Google API Client** - YouTube Data API v3

### Frontend
- **Vite** - Next-generation frontend tooling
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **React Router** - Client-side routing
- **Lucide React** - Icons

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **YouTube Data API v3 key(s)** - [Get one here](https://console.cloud.google.com/apis/credentials)

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
```

### 3. Configure Environment Variables

Edit `.env` file in the root directory:

```env
# REQUIRED: Add your YouTube API keys (comma-separated for multiple keys)
YOUTUBE_API_KEYS=your-key-1,your-key-2,your-key-3

# Optional: Customize other settings
DATABASE_URL=sqlite:///./youtube_analytics.db
SECRET_KEY=your-secret-key
```

**Getting YouTube API Keys:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable "YouTube Data API v3"
4. Go to Credentials → Create Credentials → API Key
5. Add multiple keys for better quota management (recommended: 2-3 keys)

### 4. Run Backend

```bash
cd backend

# Make sure virtual environment is activated
# The backend will automatically:
# - Create the SQLite database
# - Initialize tables
# - Start the API server
# - Start the background scheduler

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### 5. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

### 6. Start Using the System

1. Open http://localhost:5173 in your browser
2. Go to **Channels** page
3. Add a YouTube channel by URL (e.g., `https://www.youtube.com/@mkbhd`)
4. Click **Import Videos** to fetch videos from the channel
5. View analytics, trending videos, and metrics!

## 📖 Usage Guide

### Adding Channels

The system accepts various YouTube URL formats:

- `https://www.youtube.com/@handle`
- `https://www.youtube.com/channel/UCxxxxxxxx`
- `https://www.youtube.com/c/channelname`
- `https://www.youtube.com/user/username`
- Any YouTube video URL (extracts channel automatically)

### API Endpoints

**Channels:**
- `POST /api/v1/channels` - Add new channel
- `GET /api/v1/channels` - List all channels
- `GET /api/v1/channels/{id}` - Get channel details
- `POST /api/v1/channels/{id}/import-videos` - Import channel videos

**Videos:**
- `GET /api/v1/channels/{id}/videos` - List channel videos
- `GET /api/v1/videos/{id}` - Get video details

**Analytics:**
- `GET /api/v1/analytics/channels/{id}/metrics` - Channel metrics
- `GET /api/v1/analytics/videos/{id}/metrics` - Video metrics
- `GET /api/v1/analytics/trending/videos` - Trending videos
- `GET /api/v1/analytics/compare/channels` - Compare channels

**System:**
- `GET /quota-status` - YouTube API quota status across all keys
- `GET /health` - Health check

Full API documentation with interactive testing: **http://localhost:8000/docs**

### Background Tasks

The system automatically runs these tasks:

- **Daily at 2 AM**: Update all channel statistics
- **Daily at 3 AM**: Update video statistics (recent videos prioritized)
- **Every 6 hours**: Check alert rules

Schedule is configurable via `SNAPSHOT_SCHEDULE_CRON` in `.env`

## 🔑 Multi-API Key Management

One of the key features is intelligent management of multiple YouTube API keys:

### Why Multiple Keys?

- YouTube API has a default quota of **10,000 units/day per key**
- Multiple keys give you more total quota (e.g., 3 keys = 30,000 units/day)
- System handles key rotation, quota tracking, and failover automatically

### How It Works

1. **Round-Robin Rotation**: Requests are distributed across all available keys
2. **Quota Tracking**: Each key's usage is monitored in real-time
3. **Automatic Failover**: If a key hits quota limit, it's disabled until reset
4. **Daily Reset**: Quotas reset automatically (YouTube resets at midnight Pacific Time)
5. **Error Handling**: Failed requests trigger key disabling when appropriate

### Monitoring Quota

- View quota status on the Dashboard
- Check `/quota-status` API endpoint
- Each key shows: used, remaining, percentage, and status

### Quota Costs

- Channel details: 1 unit
- Video list: 1 unit
- Video details: 1 unit per batch (up to 50 videos)
- Comments: 1 unit per request

**Example**: Adding a channel with 100 videos costs ~3 units (1 for channel + 2 for videos batched).

## 📊 Data Collection Strategy

### Initial Import
When you add a channel:
1. Channel information is fetched and stored
2. Videos are imported (configurable limit, default 100 for MVP)
3. Initial statistics snapshot is created

### Periodic Updates
- **Recent videos** (< 7 days old): Updated daily
- **Older videos**: Updated less frequently (configurable)
- **Channels**: Statistics updated daily

### Caching
- API responses are cached in memory (TTL: 1-6 hours)
- Reduces API quota usage
- Configurable via `CACHE_TTL_*` settings

## 🗃️ Database Schema

### Main Tables
- `channels` - Channel metadata
- `videos` - Video metadata
- `channel_stats_snapshots` - Historical channel statistics
- `video_stats_snapshots` - Historical video statistics

### Additional Tables
- `comments` - Video comments (for future AI analysis)
- `alert_rules` - Configurable alert rules
- `alerts` - Triggered alerts
- `notification_targets` - External notification endpoints

### Upgrading to PostgreSQL

The code is designed to work with both SQLite and PostgreSQL. To upgrade:

1. Install PostgreSQL
2. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/youtube_analytics
   ```
3. Install async driver: `pip install asyncpg`
4. Restart the application

## 🧪 Development

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

### Project Structure

```
youtube-analytics/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── models/          # SQLModel ORM models
│   │   ├── services/
│   │   │   ├── data_ingestion/  # YouTube API integration
│   │   │   ├── analytics/       # Metrics calculation
│   │   │   ├── alerts/          # Alert system
│   │   │   ├── future_ai/       # AI interfaces (planned)
│   │   │   └── api_key_manager.py  # Multi-key management
│   │   ├── core/            # Config, database
│   │   ├── scheduler.py     # APScheduler tasks
│   │   └── main.py          # FastAPI app entry
│   ├── tests/               # Unit tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── lib/             # API client, utils
│   │   ├── types/           # TypeScript types
│   │   ├── App.tsx          # Main app component
│   │   └── main.tsx         # Entry point
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 🔮 Future Enhancements

### Phase 2: YouTube Analytics API (Planned)
- OAuth integration for own channels
- Detailed analytics (traffic sources, demographics)
- Revenue data (for monetized channels)

### Phase 3: AI Integration (Planned)
- Comment sentiment analysis (OpenAI/Anthropic)
- Content idea generation
- Automated script writing
- Trend prediction

The system includes stub interfaces in `backend/app/services/future_ai/` that can be easily swapped with real implementations.

### Phase 4: Notifications (Planned)
- Webhook support
- Telegram/Slack/Discord notifications
- Email alerts
- Custom notification rules

## 🐛 Troubleshooting

### Backend won't start

**Error:** `YOUTUBE_API_KEYS` not found
- **Solution:** Create `.env` file in root directory and add your API keys

**Error:** Import errors
- **Solution:** Make sure virtual environment is activated and run `pip install -r requirements.txt`

### Frontend won't start

**Error:** Module not found
- **Solution:** Run `npm install` in frontend directory

**Error:** Can't connect to backend
- **Solution:** Make sure backend is running on port 8000

### API Quota Issues

**Error:** All API keys exhausted
- **Solution:**
  - Wait for daily quota reset (midnight Pacific Time)
  - Add more API keys to `.env`
  - Reduce update frequency

### Database Issues

**Error:** Database locked
- **Solution:** SQLite doesn't support high concurrency. Consider upgrading to PostgreSQL for production use.

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📧 Support

For issues and questions, create an issue in GitHub.

---

**Built with ❤️ for YouTube content creators and analysts**
