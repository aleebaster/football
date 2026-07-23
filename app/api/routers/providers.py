"""Providers Router — provider status endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_provider_service
from app.application.dto.provider_dto import ProviderListDTO
from app.application.services.provider_service import ProviderService

router = APIRouter()


@router.get("/providers", response_model=ProviderListDTO)
async def get_providers(
    service: ProviderService = Depends(get_provider_service),
) -> ProviderListDTO:
    """Get all registered providers and their health status."""
    return service.get_providers()
