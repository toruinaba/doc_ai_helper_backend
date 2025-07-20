"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

from ..core.config import settings

# SQLAlchemy Base class for models
Base = declarative_base()

# SQLite(n^¨ó¸ó-š
if settings.database_url.startswith("sqlite"):
    # SQLite(nyŠ-š
    async_engine = create_async_engine(
        settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
        echo=settings.database_echo,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
else:
    # PostgreSQLIn4
    async_engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
    )

# ^»Ã·çóáü«ü
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ¨ó¸óAlembic(	
sync_engine = create_engine(
    settings.database_url.replace("+aiosqlite", ""),
    echo=settings.database_echo,
    poolclass=StaticPool if settings.database_url.startswith("sqlite") else None,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


async def get_db() -> AsyncSession:
    """
    Database session dependency for FastAPI.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    """
    await async_engine.dispose()