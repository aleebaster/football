"""Application settings using Pydantic v2.

Centralized configuration management with environment variable support.
All settings are loaded from .env file or environment variables.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseSettings):
    """Telegram bot configuration."""

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_")

    bot_token: str = Field(..., description="Telegram Bot API token")
    admin_id: int = Field(..., description="Telegram admin user ID")


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="sqlite+aiosqlite:///football.db",
        description="Database connection URL"
    )
    echo: bool = Field(default=False, description="Enable SQL echo logging")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max pool overflow")


class LogSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        description="Log format"
    )
    rotation: str = Field(default="100 MB", description="Log rotation size")
    retention: str = Field(default="30 days", description="Log retention period"
    )
    compression: str = Field(default="gz", description="Log compression format")


class CacheSettings(BaseSettings):
    """Cache configuration."""

    model_config = SettingsConfigDict(env_prefix="CACHE_")

    backend: str = Field(default="memory", description="Cache backend (memory/redis)")
    ttl: int = Field(default=300, description="Cache TTL in seconds")
    max_size: int = Field(default=1000, description="Max cache entries for memory backend")
    redis_url: str | None = Field(default=None, description="Redis connection URL")


class SchedulerSettings(BaseSettings):
    """Scheduler configuration."""

    model_config = SettingsConfigDict(env_prefix="SCHEDULER_")

    enabled: bool = Field(default=True, description="Enable scheduler")


class DashboardSettings(BaseSettings):
    """Dashboard/FastAPI configuration."""

    model_config = SettingsConfigDict(env_prefix="DASHBOARD_")

    host: str = Field(default="0.0.0.0", description="Dashboard host")
    port: int = Field(default=8000, description="Dashboard port")
    debug: bool = Field(default=False, description="Enable debug mode")


class AnalysisSettings(BaseSettings):
    """Betting analysis parameters."""

    model_config = SettingsConfigDict(env_prefix="ANALYSIS_")

    update_interval: int = Field(default=300, description="Update interval in seconds")
    min_expected_value: float = Field(default=5.0, description="Minimum expected value threshold")
    min_profit: float = Field(default=3.0, description="Minimum profit threshold")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    language: str = Field(default="uk", description="Application language")
    project_name: str = Field(default="Football Analysis", description="Project name")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "logs")

    # Sub-configurations
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LogSettings = Field(default_factory=LogSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    dashboard: DashboardSettings = Field(default_factory=DashboardSettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)

    def model_post_init(self, __context: object) -> None:
        """Create necessary directories after initialization."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get application settings instance.

    Returns:
        Settings: Application settings loaded from environment variables.
    """
    return Settings()
