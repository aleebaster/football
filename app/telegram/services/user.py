"""User service for Telegram bot.

Provides CRUD operations for user management.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.base import CacheManager
from app.core.base import BaseService
from app.database.models.user import User
from app.logging import get_logger

logger = get_logger(__name__)


class UserService(BaseService):
    """Service for user management operations."""

    def __init__(self, session: AsyncSession, cache: CacheManager) -> None:
        """Initialize user service.

        Args:
            session: Database session.
            cache: Cache manager instance.
        """
        super().__init__(session, cache)
        self._cache_prefix = "user:"

    async def get_by_id(self, id: Any) -> User | None:
        """Get user by ID.

        Args:
            id: User UUID.

        Returns:
            User or None if not found.
        """
        result = await self._session.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID.

        Returns:
            User or None if not found.
        """
        cache_key = f"{self._cache_prefix}tg:{telegram_id}"
        cached = await self._cache.get(cache_key)
        if cached and isinstance(cached, User):
            return cached

        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            await self._cache.set(cache_key, user, ttl=300)
        return user

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Get all users with pagination.

        Args:
            limit: Maximum number of users.
            offset: Number of users to skip.

        Returns:
            List of users.
        """
        result = await self._session.execute(select(User).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> User:
        """Create a new user.

        Args:
            data: User data dictionary.

        Returns:
            Created user.
        """
        user = User(**data)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)

        cache_key = f"{self._cache_prefix}tg:{user.telegram_id}"
        await self._cache.set(cache_key, user, ttl=300)

        logger.info(f"Created new user: {user.telegram_id}")
        return user

    async def update(self, id: Any, data: dict[str, Any]) -> User | None:
        """Update a user.

        Args:
            id: User UUID.
            data: Updated data dictionary.

        Returns:
            Updated user or None if not found.
        """
        user = await self.get_by_id(id)
        if not user:
            return None

        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(user)

        # Update cache
        cache_key = f"{self._cache_prefix}tg:{user.telegram_id}"
        await self._cache.set(cache_key, user, ttl=300)

        logger.info(f"Updated user: {user.telegram_id}")
        return user

    async def delete(self, id: Any) -> bool:
        """Delete a user.

        Args:
            id: User UUID.

        Returns:
            True if deleted, False if not found.
        """
        user = await self.get_by_id(id)
        if not user:
            return False

        telegram_id = user.telegram_id
        await self._session.delete(user)
        await self._session.commit()

        # Remove from cache
        cache_key = f"{self._cache_prefix}tg:{telegram_id}"
        await self._cache.delete(cache_key)

        logger.info(f"Deleted user: {telegram_id}")
        return True

    async def create_or_update(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
    ) -> User | None:
        """Create or update user from Telegram data.

        Args:
            telegram_id: Telegram user ID.
            username: Telegram username.
            first_name: User's first name.
            last_name: User's last name.
            language_code: User's language code.

        Returns:
            Created or updated user.
        """
        user = await self.get_by_telegram_id(telegram_id)

        if user is None:
            user = await self.create(
                {
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "language_code": language_code or "uk",
                }
            )
        else:
            update_data: dict[str, Any] = {}
            if username is not None:
                update_data["username"] = username
            if first_name is not None:
                update_data["first_name"] = first_name
            if last_name is not None:
                update_data["last_name"] = last_name
            if language_code is not None:
                update_data["language_code"] = language_code

            if update_data:
                result = await self.update(user.id, update_data)
                if result is not None:
                    user = result

        return user

    async def update_last_activity(self, telegram_id: int) -> None:
        """Update user's last activity timestamp.

        Args:
            telegram_id: Telegram user ID.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.updated_at = datetime.now(UTC)
            await self._session.commit()

    async def update_language(self, telegram_id: int, language: str) -> User | None:
        """Update user's language preference.

        Args:
            telegram_id: Telegram user ID.
            language: Language code.

        Returns:
            Updated user or None.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return await self.update(user.id, {"language_code": language})
        return None
