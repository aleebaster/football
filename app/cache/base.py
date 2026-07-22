"""Base cache interface.

Provides abstract cache backend that can be implemented
by memory cache or Redis cache.
"""

from abc import ABC, abstractmethod
from typing import Any


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value by key.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value with optional TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key.

        Returns:
            True if exists, False otherwise.
        """
        ...

    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Key pattern (default: all keys).

        Returns:
            List of matching keys.
        """
        ...


class CacheManager:
    """Manages cache backend instances."""

    def __init__(self, backend: CacheBackend) -> None:
        """Initialize cache manager.

        Args:
            backend: Cache backend implementation.
        """
        self._backend = backend

    @property
    def backend(self) -> CacheBackend:
        """Get the cache backend."""
        return self._backend

    async def get(self, key: str) -> Any | None:
        """Get value by key."""
        return await self._backend.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value with optional TTL."""
        await self._backend.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete value by key."""
        return await self._backend.delete(key)

    async def clear(self) -> None:
        """Clear all cached values."""
        await self._backend.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self._backend.exists(key)

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern."""
        return await self._backend.keys(pattern)

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: int | None = None,
    ) -> Any:
        """Get value from cache or compute and cache it.

        Args:
            key: Cache key.
            factory: Callable that returns the value if not cached.
            ttl: Time to live in seconds.

        Returns:
            Cached or computed value.
        """
        value = await self._backend.get(key)
        if value is not None:
            return value

        if callable(factory):
            import inspect

            if inspect.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
        else:
            value = factory

        await self._backend.set(key, value, ttl)
        return value
