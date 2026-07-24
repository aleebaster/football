"""Live Router — REST API endpoints for the Live Engine.

Endpoints:
    GET /live                — Live engine status
    GET /live/matches        — Active live matches
    GET /live/workers        — Worker information
    GET /live/events         — Recent events
    GET /live/metrics        — Live engine metrics
    GET /live/heartbeat      — Heartbeat information
    GET /live/state          — Current match states
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_live_service
from app.application.dto.live_dto import (
    HeartbeatDTO,
    LiveEventDTO,
    LiveMatchDTO,
    LiveMetricsDTO,
    LiveStatusDTO,
    WorkerDTO,
)
from app.application.services.live_service import LiveService

router = APIRouter()


@router.get("/live", response_model=LiveStatusDTO)
async def get_live_status(
    service: LiveService = Depends(get_live_service),
) -> LiveStatusDTO:
    """Get overall Live Engine status."""
    return service.get_live_status()


@router.get("/live/matches", response_model=list[LiveMatchDTO])
async def get_live_matches(
    service: LiveService = Depends(get_live_service),
) -> list[LiveMatchDTO]:
    """Get all active live matches."""
    return await service.get_live_matches()


@router.get("/live/workers", response_model=list[WorkerDTO])
async def get_live_workers(
    service: LiveService = Depends(get_live_service),
) -> list[WorkerDTO]:
    """Get worker information."""
    return service.get_workers()


@router.get("/live/events", response_model=list[LiveEventDTO])
async def get_live_events(
    limit: int = 50,
    service: LiveService = Depends(get_live_service),
) -> list[LiveEventDTO]:
    """Get recent live events."""
    return service.get_events(limit=limit)


@router.get("/live/metrics", response_model=LiveMetricsDTO)
async def get_live_metrics(
    service: LiveService = Depends(get_live_service),
) -> LiveMetricsDTO:
    """Get live engine metrics."""
    return service.get_metrics()


@router.get("/live/heartbeat", response_model=HeartbeatDTO)
async def get_live_heartbeat(
    service: LiveService = Depends(get_live_service),
) -> HeartbeatDTO:
    """Get heartbeat information."""
    return service.get_heartbeat()


@router.get("/live/state")
async def get_live_state(
    service: LiveService = Depends(get_live_service),
) -> dict[str, str]:
    """Get current match states."""
    return await service.get_state()
