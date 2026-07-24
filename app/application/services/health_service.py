"""Health Service — provides system health status."""

from app.application.dto.health_dto import HealthDTO
from app.application.mapper import Mapper
from app.core.container import get_container
from app.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    """Provides system health information."""

    def get_health(self) -> HealthDTO:
        container = get_container()

        # Gather provider health info via public API
        provider_health: list[dict[str, object]] = []
        try:
            registry = container.provider_registry
            for name, provider in registry.items():
                health = provider.health_info
                provider_health.append(
                    {
                        "name": name,
                        "status": health.status.value,
                        "success_rate": health.success_rate / 100.0,
                        "avg_response_ms": health.average_response_time * 1000,
                        "consecutive_failures": health.consecutive_failures,
                    }
                )
        except Exception:
            logger.warning("Failed to gather provider health info", exc_info=True)

        return Mapper.to_health_dto(
            providers=provider_health,
            cache_entries=0,
        )
