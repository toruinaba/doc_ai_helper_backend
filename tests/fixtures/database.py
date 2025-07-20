"""
Database fixtures for testing.

Provides test database setup and cleanup utilities.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from doc_ai_helper_backend.db.database import Base
from doc_ai_helper_backend.db.models import Repository as RepositoryModel


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def sample_repository_in_db(test_db_session: AsyncSession) -> RepositoryModel:
    """Create a sample repository in the test database."""
    from datetime import datetime
    
    repository = RepositoryModel(
        name="test-repo",
        owner="test-owner",
        service_type="github",
        url="https://github.com/test-owner/test-repo",
        base_url=None,
        default_branch="main",
        root_path="docs",
        description="Test repository",
        is_public=True,
        supported_branches_json=["main", "develop"],
        repo_metadata={"project_type": "documentation"},
    )
    
    test_db_session.add(repository)
    await test_db_session.commit()
    await test_db_session.refresh(repository)
    
    return repository


@pytest.fixture
async def clean_database(test_db_session: AsyncSession):
    """Clean database before test."""
    from sqlalchemy import text
    
    # Delete all data
    await test_db_session.execute(text("DELETE FROM repositories"))
    await test_db_session.commit()
    yield
    # Clean after test as well
    await test_db_session.execute(text("DELETE FROM repositories"))
    await test_db_session.commit()