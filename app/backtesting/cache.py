"""Backtesting Cache — caches backtest results."""

from typing import Any

from app.cache.base import CacheManager
from app.logging import get_logger

logger = get_logger(__name__)

CACHE_PREFIX = "backtest:"
DEFAULT_TTL = 600  # 10 minutes


class BacktestCache:
    """Caches backtest results using the Cache Layer."""

    def __init__(self, cache_manager: CacheManager | None = None) -> None:
        self._cache = cache_manager

    async def get(self, key: str) -> Any | None:
        """Get cached backtest data.

        Args:
            key: Cache key.

        Returns:
            Cached data or None.
        """
        if self._cache is None:
            return None
        return await self._cache.get(f"{CACHE_PREFIX}{key}")

    async def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Cache backtest data.

        Args:
            key: Cache key.
            value: Data to cache.
            ttl: Time to live in seconds.
        """
        if self._cache is None:
            return
        await self._cache.set(f"{CACHE_PREFIX}{key}", value, ttl)

    async def invalidate(self, key: str) -> bool:
        """Invalidate cached backtest data.

        Args:
            key: Cache key.

        Returns:
            True if invalidated.
        """
        if self._cache is None:
            return False
        return await self._cache.delete(f"{CACHE_PREFIX}{key}")

    async def clear(self) -> None:
        """Clear all cached backtest data."""
        if self._cache is None:
            return
        keys = await self._cache.keys(f"{CACHE_PREFIX}*")
        for key in keys:
            await self._cache.delete(key)
        logger.info(f"Cleared {len(keys)} cached backtest entries")
