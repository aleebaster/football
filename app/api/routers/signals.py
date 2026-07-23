"""Signals Router — signal endpoints."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_signal_service
from app.application.dto.signal_dto import SignalDTO, SignalListDTO
from app.application.services.signal_service import SignalService

router = APIRouter()


@router.get("/signals", response_model=SignalListDTO)
async def get_signals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: SignalService = Depends(get_signal_service),
) -> SignalListDTO:
    """Get paginated list of active signals."""
    return await service.get_signals(page=page, page_size=page_size)


@router.get("/signals/{signal_id}", response_model=SignalDTO)
async def get_signal(
    signal_id: str,
    service: SignalService = Depends(get_signal_service),
) -> SignalDTO:
    """Get a specific signal by ID."""
    result = await service.get_signal(signal_id)
    if result is None:
        from app.api.exceptions import APINotFoundError

        raise APINotFoundError(f"Signal {signal_id} not found")
    return result
