"""Pytest configuration and shared fixtures.

Provides test configuration, database fixtures, and mock utilities.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.database.base import Base
from app.database.session import DatabaseSessionManager
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Any:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_manager() -> AsyncGenerator[DatabaseSessionManager, None]:
    """Create test database manager with in-memory SQLite."""
    manager = DatabaseSessionManager(database_url="sqlite+aiosqlite:///:memory:")
    await manager.connect()
    async with manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield manager
    await manager.disconnect()


@pytest_asyncio.fixture
async def test_session(test_db_manager: DatabaseSessionManager) -> AsyncGenerator[Any, None]:
    """Get test database session."""
    async for session in test_db_manager.get_session():
        yield session


@pytest.fixture
def test_cache() -> CacheManager:
    """Get test cache manager."""
    backend = MemoryCache(max_size=100, default_ttl=60)
    return CacheManager(backend)


@pytest_asyncio.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Get test HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
