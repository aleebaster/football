"""Health Router — system health endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_health_service
from app.application.dto.health_dto import HealthDTO
from app.application.services.health_service import HealthService

router = APIRouter()


@router.get("/health", response_model=HealthDTO)
async def health_check(
    service: HealthService = Depends(get_health_service),
) -> HealthDTO:
    """Get system health status.

    Returns provider health, cache status, engine status, and database status.
    """
    return service.get_health()
