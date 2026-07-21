"""Base service class for all application services.

Provides common functionality and interfaces for services.
"""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.base import CacheManager


class BaseService(ABC):
    """Base class for all application services.

    Provides:
        - Database session management
        - Cache integration
        - Common CRUD operations
    """

    def __init__(self, session: AsyncSession, cache: CacheManager) -> None:
        """Initialize the service.

        Args:
            session: Database session.
            cache: Cache manager instance.
        """
        self._session = session
        self._cache = cache

    @property
    def session(self) -> AsyncSession:
        """Get the database session."""
        return self._session

    @property
    def cache(self) -> CacheManager:
        """Get the cache manager."""
        return self._cache

    @abstractmethod
    async def get_by_id(self, id: Any) -> Any | None:
        """Get entity by ID.

        Args:
            id: Entity ID.

        Returns:
            Entity or None if not found.
        """
        ...

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Any]:
        """Get all entities with pagination.

        Args:
            limit: Maximum number of entities.
            offset: Number of entities to skip.

        Returns:
            List of entities.
        """
        ...

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> Any:
        """Create a new entity.

        Args:
            data: Entity data.

        Returns:
            Created entity.
        """
        ...

    @abstractmethod
    async def update(self, id: Any, data: dict[str, Any]) -> Any | None:
        """Update an entity.

        Args:
            id: Entity ID.
            data: Updated data.

        Returns:
            Updated entity or None if not found.
        """
        ...

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete an entity.

        Args:
            id: Entity ID.

        Returns:
            True if deleted, False if not found.
        """
        ...
