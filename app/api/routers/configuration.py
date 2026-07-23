"""Configuration Router — application configuration endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_configuration_service
from app.application.dto.configuration_dto import ConfigurationDTO
from app.application.services.configuration_service import ConfigurationService

router = APIRouter()


@router.get("/configuration", response_model=ConfigurationDTO)
async def get_configuration(
    service: ConfigurationService = Depends(get_configuration_service),
) -> ConfigurationDTO:
    """Get application configuration (read-only)."""
    return service.get_configuration()
