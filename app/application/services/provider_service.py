"""Provider Service — provides provider data."""

from app.application.dto.provider_dto import ProviderDTO, ProviderListDTO
from app.application.mapper import Mapper
from app.core.container import get_container


class ProviderService:
    """Provides provider data through the Provider Layer."""

    def get_providers(self) -> ProviderListDTO:
        container = get_container()
        registry = container.provider_registry

        providers: list[ProviderDTO] = []
        healthy = 0
        degraded = 0
        unhealthy = 0

        for name, provider in registry._providers.items():
            health = provider.health_info
            dto = Mapper.to_provider_dto(name, health)
            providers.append(dto)

            if health.status.value == "healthy":
                healthy += 1
            elif health.status.value == "degraded":
                degraded += 1
            else:
                unhealthy += 1

        return ProviderListDTO(
            providers=providers,
            total=len(providers),
            healthy=healthy,
            degraded=degraded,
            unhealthy=unhealthy,
        )
