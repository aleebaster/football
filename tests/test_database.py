"""Tests for database module."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.database.base import Base
from app.database.models import User
from app.database.session import DatabaseSessionManager


class TestDatabaseModels:
    """Tests for database models and table creation."""

    @pytest.mark.asyncio
    async def test_metadata_has_models(self) -> None:
        """Test that Base metadata contains all registered models."""
        table_names = Base.metadata.tables.keys()
        assert "users" in table_names

    @pytest.mark.asyncio
    async def test_user_model_columns(self) -> None:
        """Test User model has all required columns."""
        columns = [c.name for c in User.__table__.columns]
        assert "id" in columns
        assert "telegram_id" in columns
        assert "username" in columns
        assert "first_name" in columns
        assert "last_name" in columns
        assert "language_code" in columns
        assert "is_active" in columns
        assert "is_admin" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    @pytest.mark.asyncio
    async def test_create_tables_sqlalchemy(self) -> None:
        """Test that SQLAlchemy can create all tables from metadata."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Verify tables were created by checking metadata
        async with engine.connect() as conn:
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    __import__("sqlalchemy").text(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            )
            table_names = [row[0] for row in result]
            assert "users" in table_names

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_database_session_manager(self) -> None:
        """Test DatabaseSessionManager creates tables."""
        manager = DatabaseSessionManager(database_url="sqlite+aiosqlite:///:memory:")
        await manager.connect()
        await manager.create_tables()

        # Verify tables exist
        async with manager.engine.connect() as conn:
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    __import__("sqlalchemy").text(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
            )
            table_names = [row[0] for row in result]
            assert "users" in table_names

        await manager.disconnect()
