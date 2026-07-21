"""In-memory cache implementation."""

import fnmatch
import time
from typing import Any

from app.cache.base import CacheBackend
from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support."""

    def __init__(self, max_size: int | None = None, default_ttl: int | None = None) -> None:
        """Initialize memory cache."""
        self._cache: dict[str, tuple[Any, float]] = {}
        self._max_size: int = max_size or settings.cache.max_size
        self._default_ttl: int = default_ttl or settings.cache.ttl

    async def get(self, key: str) -> Any | None:
        """Get value by key."""
        if key not in self._cache:
            return None

        value, expire_time = self._cache[key]
        if time.time() > expire_time:
            del self._cache[key]
            return None

        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value with optional TTL."""
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._evict_oldest()

        expire_time = time.time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expire_time)

    async def delete(self, key: str) -> bool:
        """Delete value by key."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if key not in self._cache:
            return False

        _, expire_time = self._cache[key]
        if time.time() > expire_time:
            del self._cache[key]
            return False

        return True

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern."""
        current_time = time.time()
        valid_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if current_time <= expire_time
        ]

        if pattern == "*":
            return valid_keys

        return [key for key in valid_keys if fnmatch.fnmatch(key, pattern)]

    async def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def _evict_oldest(self) -> None:
        """Evict the oldest entry from cache."""
        if not self._cache:
            return

        oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
