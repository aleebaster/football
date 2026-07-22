"""Provider-specific cache layer.

Caches football data with different TTL per type.
Uses existing CacheManager infrastructure.
"""

from typing import Any

from app.cache.base import CacheManager
from app.logging import get_logger

logger = get_logger(__name__)

# Cache TTL per data type (seconds)
CACHE_TTL: dict[str, int] = {
    "live": 30,
    "fixtures": 300,
    "fixture_detail": 60,
    "standings": 3600,
    "teams": 86400,
    "competitions": 86400,
    "statistics": 300,
    "events": 60,
    "odds": 120,
    "head_to_head": 7200,
    "search": 3600,
    "player": 86400,
}

PREFIX = "provider"


class ProviderCache:
    """Cache wrapper for provider data with type-based TTL."""

    def __init__(self, cache: CacheManager) -> None:
        self._cache = cache

    def _make_key(self, provider: str, data_type: str, key: str) -> str:
        return f"{PREFIX}:{provider}:{data_type}:{key}"

    async def get(self, provider: str, data_type: str, key: str) -> Any | None:
        cache_key = self._make_key(provider, data_type, key)
        value = await self._cache.get(cache_key)
        if value is not None:
            logger.debug(f"Cache HIT: {cache_key}")
        else:
            logger.debug(f"Cache MISS: {cache_key}")
        return value

    async def set(self, provider: str, data_type: str, key: str, value: Any) -> None:
        ttl = CACHE_TTL.get(data_type, 300)
        cache_key = self._make_key(provider, data_type, key)
        await self._cache.set(cache_key, value, ttl=ttl)
        logger.debug(f"Cache SET: {cache_key} (TTL={ttl}s)")

    async def invalidate(self, provider: str, data_type: str | None = None) -> int:
        pattern = (
            f"{PREFIX}:{provider}:{data_type}:*"
            if data_type
            else f"{PREFIX}:{provider}:*"
        )
        keys = await self._cache.keys(pattern)
        for key in keys:
            await self._cache.delete(key)
        logger.debug(f"Cache invalidated {len(keys)} keys for {provider}")
        return len(keys)

    async def clear(self) -> None:
        keys = await self._cache.keys(f"{PREFIX}:*")
        for key in keys:
            await self._cache.delete(key)
        logger.info(f"Provider cache cleared ({len(keys)} keys)")
