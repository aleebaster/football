"""Live Dashboard Router — REST API endpoints for Live Engine dashboard pages.

All endpoints follow the pipeline:
    LiveService → DTO → LiveDashboardPresenter → Response

Dashboard does NOT access Live Engine directly — only through Application Layer.

Endpoints:
    GET /dashboard/live                — Live engine status overview
    GET /dashboard/live/matches        — Live matches page
    GET /dashboard/live/workers        — Workers page
    GET /dashboard/live/heartbeat      — Heartbeat page
    GET /dashboard/live/metrics        — Live metrics page
    GET /dashboard/live/events         — Recent events page
    GET /dashboard/live/providers      — Provider health page
    GET /dashboard/live/queue          — Queue status page
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_live_service, get_provider_service
from app.application.services.live_service import LiveService
from app.application.services.provider_service import ProviderService
from app.dashboard.presenters import LiveDashboardPresenter

router = APIRouter()


@router.get("/dashboard/live")
async def live_overview(
    service: LiveService = Depends(get_live_service),
) -> dict[str, object]:
    """Live engine status overview page."""
    status = service.get_live_status()
    return LiveDashboardPresenter.present_queue_status(status)


@router.get("/dashboard/live/matches")
async def live_matches_page(
    service: LiveService = Depends(get_live_service),
) -> dict[str, object]:
    """Live matches dashboard page."""
    matches = await service.get_live_matches()
    status = service.get_live_status()
    return LiveDashboardPresenter.present_live_matches(
        matches, active_count=status.active_matches
    )


@router.get("/dashboard/live/workers")
async def live_workers_page(
    service: LiveService = Depends(get_live_service),
) -> dict[str, object]:
    """Workers dashboard page."""
    workers = await service.get_workers()
    return LiveDashboardPresenter.present_workers(workers)


@router.get("/dashboard/live/heartbeat")
async def live_heartbeat_page(
    service: LiveService = Depends(get_live_service),
) -> dict[str, object]:
    """Heartbeat dashboard page."""
    heartbeat = service.get_heartbeat()
    return LiveDashboardPresenter.present_heartbeat(heartbeat)


@router.get("/dashboard/live/metrics")
async def live_metrics_page(
    service: LiveService = Depends(get_live_service),
) -> dict[str, object]:
    """Live metrics dashboard page."""
    metrics = service.get_metrics()
    return LiveDashboardPresenter.present_metrics(metrics)


@router.get("/dashboard/live/events")
async def live_events_page(
    limit: int = 50,
    service: LiveService = Depends(get_live_service),
) -> dict[str, object]:
    """Recent events dashboard page."""
    events = service.get_events(limit=limit)
    return LiveDashboardPresenter.present_recent_events(events)


@router.get("/dashboard/live/providers")
async def live_providers_page(
    provider_service: ProviderService = Depends(get_provider_service),
) -> dict[str, object]:
    """Provider health dashboard page."""
    provider_list = provider_service.get_providers()
    return LiveDashboardPresenter.present_provider_health(provider_list.providers)


@router.get("/dashboard/live/queue")
async def live_queue_page(
    service: LiveService = Depends(get_live_service),
) -> dict[str, object]:
    """Queue status dashboard page."""
    status = service.get_live_status()
    return LiveDashboardPresenter.present_queue_status(status)
