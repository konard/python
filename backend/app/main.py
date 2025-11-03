"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"Starting {settings.app_name}...")
    yield
    # Shutdown
    print("Shutting down...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="YouTube Channel Analytics System",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers (will be added later)
# from app.api.v1 import channels, videos, analytics, alerts
# app.include_router(channels.router, prefix="/api/v1", tags=["channels"])
# app.include_router(videos.router, prefix="/api/v1", tags=["videos"])
# app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
# app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
