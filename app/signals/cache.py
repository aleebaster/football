"""Cache layer for Signal Engine results."""

from typing import Any

from app.cache.base import CacheManager
from app.logging import get_logger

logger = get_logger(__name__)

SIGNAL_CACHE_PREFIX = "signal:"
SIGNAL_CACHE_TTL = 300  # 5 minutes


class SignalCache:
    """Caches signal results to avoid recomputation."""

    def __init__(self, cache: CacheManager) -> None:
        self._cache = cache

    def _key(self, fixture_id: int) -> str:
        return f"{SIGNAL_CACHE_PREFIX}{fixture_id}"

    async def get(self, fixture_id: int) -> list[dict[str, Any]] | None:
        """Get cached signals for a fixture."""
        return await self._cache.get(self._key(fixture_id))

    async def set(self, fixture_id: int, data: list[dict[str, Any]]) -> None:
        """Cache signals for a fixture."""
        await self._cache.set(self._key(fixture_id), data, SIGNAL_CACHE_TTL)

    async def invalidate(self, fixture_id: int) -> None:
        """Invalidate cached signals for a fixture."""
        await self._cache.delete(self._key(fixture_id))

    async def invalidate_all(self) -> None:
        """Invalidate all cached signals."""
        keys = await self._cache.keys(f"{SIGNAL_CACHE_PREFIX}*")
        for key in keys:
            await self._cache.delete(key)
