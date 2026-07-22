"""Cache layer for Prediction Engine results."""

from typing import Any

from app.cache.base import CacheManager
from app.logging import get_logger

logger = get_logger(__name__)

PREDICTION_CACHE_PREFIX = "prediction:"
PREDICTION_CACHE_TTL = 600  # 10 minutes


class PredictionCache:
    """Caches prediction results to avoid recomputation."""

    def __init__(self, cache: CacheManager) -> None:
        self._cache = cache

    def _key(self, fixture_id: int) -> str:
        return f"{PREDICTION_CACHE_PREFIX}{fixture_id}"

    async def get(self, fixture_id: int) -> dict[str, Any] | None:
        return await self._cache.get(self._key(fixture_id))

    async def set(self, fixture_id: int, data: dict[str, Any]) -> None:
        await self._cache.set(self._key(fixture_id), data, PREDICTION_CACHE_TTL)

    async def invalidate(self, fixture_id: int) -> None:
        await self._cache.delete(self._key(fixture_id))
