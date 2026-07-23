"""Configuration DTO — application configuration for API responses."""

from pydantic import BaseModel


class ConfigurationDTO(BaseModel):
    """Application configuration for API response."""

    project_name: str = "Football Analysis"
    version: str = "0.1.0"
    debug: bool = False
    language: str = "uk"

    # Provider config
    primary_provider: str = "mock"
    api_football_configured: bool = False
    football_data_configured: bool = False

    # Cache config
    cache_backend: str = "memory"
    cache_ttl: int = 300

    # Dashboard config
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000

    # Scheduler
    scheduler_enabled: bool = True
