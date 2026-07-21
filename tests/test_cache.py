"""Tests for cache module."""

import time

import pytest

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache


class TestMemoryCache:
    """Tests for in-memory cache."""

    @pytest.fixture
    def cache(self) -> MemoryCache:
        """Create test cache instance."""
        return MemoryCache(max_size=10, default_ttl=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: MemoryCache) -> None:
        """Test setting and getting values."""
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache: MemoryCache) -> None:
        """Test getting nonexistent key returns None."""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache: MemoryCache) -> None:
        """Test deleting a key."""
        await cache.set("key1", "value1")
        result = await cache.delete("key1")
        assert result is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear(self, cache: MemoryCache) -> None:
        """Test clearing all cache entries."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.size() == 0

    @pytest.mark.asyncio
    async def test_exists(self, cache: MemoryCache) -> None:
        """Test checking if key exists."""
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_keys(self, cache: MemoryCache) -> None:
        """Test getting all keys."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        keys = await cache.keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

    @pytest.mark.asyncio
    async def test_ttl_expiration(self) -> None:
        """Test that entries expire after TTL using public API."""
        cache = MemoryCache(max_size=10, default_ttl=60)
        # Set with TTL=1 second
        await cache.set("key1", "value1", ttl=1)
        # Should exist immediately
        assert await cache.get("key1") == "value1"
        assert await cache.exists("key1") is True
        # Wait for expiration
        time.sleep(1.1)
        # Should be expired
        assert await cache.get("key1") is None
        assert await cache.exists("key1") is False


class TestCacheManager:
    """Tests for cache manager."""

    @pytest.fixture
    def cache_manager(self) -> CacheManager:
        """Create test cache manager instance."""
        backend = MemoryCache(max_size=10, default_ttl=60)
        return CacheManager(backend)

    @pytest.mark.asyncio
    async def test_get_or_set(self, cache_manager: CacheManager) -> None:
        """Test get_or_set with factory function."""
        result = await cache_manager.get_or_set("key1", lambda: "computed_value")
        assert result == "computed_value"

        # Second call should return cached value
        result = await cache_manager.get_or_set("key1", lambda: "different_value")
        assert result == "computed_value"
