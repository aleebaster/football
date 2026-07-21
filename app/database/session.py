"""Database session management.

Provides async session management for SQLAlchemy with support
for multiple database backends (SQLite, PostgreSQL).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


class DatabaseSessionManager:
    """Manages database engine and sessions.

    Supports switching between SQLite and PostgreSQL without code changes.
    Simply update the DATABASE_URL environment variable.
    """

    def __init__(self, database_url: str | None = None) -> None:
        """Initialize the database session manager.

        Args:
            database_url: Optional database URL override.
        """
        self._url = database_url or settings.database.url
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Create database engine and session factory."""
        connect_args = {}
        if "sqlite" in self._url:
            connect_args["check_same_thread"] = False

        self._engine = create_async_engine(
            self._url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size if "sqlite" not in self._url else None,
            max_overflow=settings.database.max_overflow if "sqlite" not in self._url else None,
            connect_args=connect_args,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        """Dispose of the database engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine instance.

        Returns:
            AsyncEngine: The database engine.

        Raises:
            RuntimeError: If engine is not initialized.
        """
        if self._engine is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._engine

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session.

        Yields:
            AsyncSession: A database session.
        """
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """Create all database tables."""
        from app.database.base import Base

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


# Global database session manager instance
db_manager = DatabaseSessionManager()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions.

    Yields:
        AsyncSession: A database session.
    """
    async for session in db_manager.get_session():
        yield session
