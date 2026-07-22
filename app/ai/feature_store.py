"""Feature store for caching computed features."""

from typing import Any

from app.cache.base import CacheManager
from app.logging import get_logger

logger = get_logger(__name__)

PREFIX = "ai_features"
FEATURE_TTL = 600  # 10 minutes


class FeatureStore:
    """Caches computed feature vectors to avoid redundant calculations."""

    def __init__(self, cache: CacheManager) -> None:
        self._cache = cache

    def _make_key(self, fixture_id: int) -> str:
        return f"{PREFIX}:{fixture_id}"

    async def get(self, fixture_id: int) -> dict[str, Any] | None:
        key = self._make_key(fixture_id)
        value = await self._cache.get(key)
        if value is not None:
            logger.debug(f"FeatureStore HIT: {fixture_id}")
        else:
            logger.debug(f"FeatureStore MISS: {fixture_id}")
        return value

    async def set(self, fixture_id: int, features: dict[str, Any]) -> None:
        key = self._make_key(fixture_id)
        await self._cache.set(key, features, ttl=FEATURE_TTL)
        logger.debug(f"FeatureStore SET: {fixture_id}")

    async def invalidate(self, fixture_id: int) -> None:
        key = self._make_key(fixture_id)
        await self._cache.delete(key)
        logger.debug(f"FeatureStore INVALIDATE: {fixture_id}")
