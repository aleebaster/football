"""Live Service — provides Live Engine data through the Application Layer.

Pipeline:
    REST Endpoint → LiveService → Live Engine → DTO Mapper → Response
"""

from __future__ import annotations

from app.application.dto.live_dto import (
    HeartbeatDTO,
    LiveEventDTO,
    LiveMatchDTO,
    LiveMetricsDTO,
    LiveStatusDTO,
    WorkerDTO,
)
from app.application.mapper import Mapper
from app.core.container import get_container
from app.live.models import WorkerInfo, WorkerStatus
from app.logging import get_logger

logger = get_logger(__name__)


class LiveService:
    """Provides Live Engine data through the Application Layer."""

    def get_live_status(self) -> LiveStatusDTO:
        """Get overall Live Engine status."""
        container = get_container()
        engine = container.live_engine
        status = engine.get_status()
        return Mapper.to_live_status_dto(status)

    async def get_live_matches(self) -> list[LiveMatchDTO]:
        """Get all active live matches."""
        container = get_container()
        engine = container.live_engine
        active = await engine.state.get_active_matches()
        matches = []
        for fixture_id, _state in active.items():
            match_data = await engine.state.get_match_data(fixture_id)
            if match_data:
                matches.append(Mapper.to_live_match_dto(match_data))
        return matches

    def get_workers(self) -> list[WorkerDTO]:
        """Get all worker information."""
        container = get_container()
        engine = container.live_engine
        result: list[WorkerDTO] = []
        for worker in engine.components.workers:
            info = WorkerInfo(
                worker_id=worker.worker_id,
                status=WorkerStatus.PROCESSING if worker.is_busy else WorkerStatus.IDLE,
                processed_count=worker.processed_count,
                error_count=worker.error_count,
            )
            result.append(Mapper.to_worker_dto(info))
        return result

    def get_events(self, limit: int = 50) -> list[LiveEventDTO]:
        """Get recent live events."""
        container = get_container()
        engine = container.live_engine
        events = engine.publisher.get_recent_events(limit)
        return [Mapper.to_live_event_dto(e) for e in events]

    def get_heartbeat(self) -> HeartbeatDTO:
        """Get heartbeat information."""
        container = get_container()
        engine = container.live_engine
        heartbeat = engine.heartbeat.get_info()
        return Mapper.to_heartbeat_dto(heartbeat)

    def get_metrics(self) -> LiveMetricsDTO:
        """Get live engine metrics."""
        container = get_container()
        engine = container.live_engine
        metrics = engine.metrics.get_metrics()
        return Mapper.to_live_metrics_dto(metrics)

    async def get_state(self) -> dict[str, str]:
        """Get current match states."""
        container = get_container()
        engine = container.live_engine
        active = await engine.state.get_active_matches()
        return {str(fid): state.value for fid, state in active.items()}
