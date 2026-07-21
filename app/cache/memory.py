"""In-memory cache implementation.

Provides a simple in-memory cache with TTL support.
Can be easily swapped with Redis for production use.
"""

import asyncio
import time
from typing import Any

from app.cache.base import CacheBackend
from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support.

    Features:
        - TTL-based expiration
        - LRU-like eviction when max_size is reached
        - Thread-safe operations
    """

    def __init__(
        self, max_size: int | None = None, default_ttl: int | None = None
    ) -> None:
        """Initialize memory cache.

        Args:
            max_size: Maximum number of entries (default from settings).
            default_ttl: Default TTL in seconds (default from settings).
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._max_size = max_size or settings.cache.max_size
        self._default_ttl = default_ttl or settings.cache.ttl
        self._lock = asyncio.Lock()
        logger.info(f"Memory cache initialized (max_size={self._max_size})")

    async def get(self, key: str) -> Any | None:
        """Get value by key.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found or expired.
        """
        async with self._lock:
            if key not in self._cache:
                return None

            value, expire_time = self._cache[key]
            if time.time() > expire_time:
                del self._cache[key]
                return None

            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value with optional TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds (default: self._default_ttl).
        """
        async with self._lock:
            # Evict oldest entry if max size reached
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()

            expire_time = time.time() + (ttl or self._default_ttl)
            self._cache[key] = (value, expire_time)

    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()
            logger.info("Memory cache cleared")

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key.

        Returns:
            True if exists and not expired, False otherwise.
        """
        async with self._lock:
            if key not in self._cache:
                return False

            _, expire_time = self._cache[key]
            if time.time() > expire_time:
                del self._cache[key]
                return False

            return True

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Key pattern (default: all keys).

        Returns:
            List of matching keys.
        """
        async with self._lock:
            current_time = time.time()
            valid_keys = [
                key
                for key, (_, expire_time) in self._cache.items()
                if current_time <= expire_time
            ]

            # Simple pattern matching (supports * wildcard)
            if pattern == "*":
                return valid_keys

            import fnmatch

            return [key for key in valid_keys if fnmatch.fnmatch(key, pattern)]

    async def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of entries in cache.
        """
        async with self._lock:
            return len(self._cache)

    def _evict_oldest(self) -> None:
        """Evict the oldest entry from cache."""
        if not self._cache:
            return

        oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
