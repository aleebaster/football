"""Dependency injection functions for FastAPI.

Provides injectable dependencies for services and utilities.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.config import settings
from app.database.session import db_manager

# Global cache instance
_cache: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager.

    Returns:
        CacheManager instance.
    """
    global _cache
    if _cache is None:
        backend = MemoryCache(
            max_size=settings.cache.max_size,
            default_ttl=settings.cache.ttl,
        )
        _cache = CacheManager(backend)
    return _cache


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions.

    Yields:
        AsyncSession: Database session.
    """
    async for session in db_manager.get_session():
        yield session


def get_cache() -> CacheManager:
    """Dependency for getting cache manager.

    Returns:
        CacheManager instance.
    """
    return get_cache_manager()
