"""Configuration Service — provides application configuration."""

from app.application.dto.configuration_dto import ConfigurationDTO
from app.config import settings


class ConfigurationService:
    """Provides application configuration data."""

    def get_configuration(self) -> ConfigurationDTO:
        return ConfigurationDTO(
            project_name=settings.project_name,
            version="0.1.0",
            debug=settings.debug,
            language=settings.language,
            primary_provider=settings.provider.primary_provider,
            api_football_configured=bool(settings.provider.api_football_key),
            football_data_configured=bool(settings.provider.football_data_key),
            cache_backend=settings.cache.backend,
            cache_ttl=settings.cache.ttl,
            dashboard_host=settings.dashboard.host,
            dashboard_port=settings.dashboard.port,
            scheduler_enabled=settings.scheduler.enabled,
        )
