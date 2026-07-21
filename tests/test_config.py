"""Tests for configuration module."""

import os
from unittest.mock import patch


class TestSettings:
    """Tests for application settings."""

    def test_settings_load_defaults(self) -> None:
        """Test settings load with default values."""
        from app.config.settings import Settings

        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_ADMIN_ID": "12345",
        }, clear=False):
            settings = Settings()
            assert settings.language == "uk"
            assert settings.project_name == "Football Analysis"

    def test_telegram_settings(self) -> None:
        """Test Telegram settings initialization."""
        from app.config.settings import TelegramSettings

        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_ADMIN_ID": "12345",
        }):
            settings = TelegramSettings()
            assert settings.bot_token == "test-token"
            assert settings.admin_id == 12345

    def test_database_settings_defaults(self) -> None:
        """Test database settings defaults."""
        from app.config.settings import DatabaseSettings

        settings = DatabaseSettings()
        assert "sqlite" in settings.url
        assert settings.echo is False

    def test_cache_settings_defaults(self) -> None:
        """Test cache settings defaults."""
        from app.config.settings import CacheSettings

        settings = CacheSettings()
        assert settings.backend == "memory"
        assert settings.ttl == 300
