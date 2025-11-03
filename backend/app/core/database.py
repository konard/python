"""Database connection and session management"""
from typing import AsyncGenerator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# Database URL handling - support both SQLite and PostgreSQL
database_url = settings.database_url_str

# For SQLite, use synchronous connections (simpler for MVP)
# For PostgreSQL, would use async
if database_url.startswith("sqlite"):
    # SQLite synchronous engine
    engine = create_engine(
        database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},  # Needed for SQLite
    )

    # For MVP, we'll use sync sessions wrapped in async
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=Session
    )

    async def get_db() -> AsyncGenerator[Session, None]:
        """
        Dependency for getting database sessions.
        Uses sync sessions for SQLite (wrapped in async function for compatibility)

        Usage in FastAPI:
            @app.get("/items")
            async def read_items(db: Session = Depends(get_db)):
                ...
        """
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def init_db() -> None:
        """Initialize database tables"""
        SQLModel.metadata.create_all(engine)

    def close_db() -> None:
        """Close database connections"""
        engine.dispose()

else:
    # PostgreSQL async engine (for future upgrade)
    async_database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
    async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://")

    async_engine = create_async_engine(
        async_database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        """Dependency for getting async database sessions (PostgreSQL)"""
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def init_db() -> None:
        """Initialize database tables (PostgreSQL)"""
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def close_db() -> None:
        """Close database connections (PostgreSQL)"""
        await async_engine.dispose()
