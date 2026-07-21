"""Cache module with memory and Redis backend support.

Provides a flexible caching system that can be easily swapped
between in-memory cache and Redis.
"""

from app.cache.base import CacheBackend, CacheManager
from app.cache.memory import MemoryCache

__all__ = ["CacheBackend", "CacheManager", "MemoryCache"]
