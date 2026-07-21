"""Core module with dependency injection and base classes.

Provides foundational utilities for the application.
"""

from app.core.base import BaseService
from app.core.dependencies import get_cache, get_database

__all__ = ["get_cache", "get_database", "BaseService"]
