"""AI Engine cache layer."""

from typing import Any

from app.cache.base import CacheManager
from app.logging import get_logger

logger = get_logger(__name__)

PREFIX = "ai_analysis"
ANALYSIS_TTL = 300  # 5 minutes


class AIAnalysisCache:
    """Cache wrapper for AI analysis results."""

    def __init__(self, cache: CacheManager) -> None:
        self._cache = cache

    def _make_key(self, fixture_id: int) -> str:
        return f"{PREFIX}:{fixture_id}"

    async def get(self, fixture_id: int) -> dict[str, Any] | None:
        key = self._make_key(fixture_id)
        value = await self._cache.get(key)
        if value is not None:
            logger.debug(f"AI cache HIT: {fixture_id}")
        else:
            logger.debug(f"AI cache MISS: {fixture_id}")
        return value

    async def set(self, fixture_id: int, result: dict[str, Any]) -> None:
        key = self._make_key(fixture_id)
        await self._cache.set(key, result, ttl=ANALYSIS_TTL)
        logger.debug(f"AI cache SET: {fixture_id}")

    async def invalidate(self, fixture_id: int) -> None:
        key = self._make_key(fixture_id)
        await self._cache.delete(key)
