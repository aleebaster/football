"""Live Engine — State Registry for tracking match states and worker health.

Maintains runtime state for the entire Live Engine.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.live.models import (
    HeartbeatInfo,
    LiveMatch,
    MatchState,
    WorkerInfo,
    WorkerStatus,
)
from app.logging import get_logger

logger = get_logger(__name__)


class StateRegistry:
    """Central state registry for the Live Engine.

    Tracks:
    - Active matches and their states
    - Worker status and health
    - Scheduler status
    - Provider health
    - Heartbeat timestamps
    """

    def __init__(self) -> None:
        self._match_states: dict[int, MatchState] = {}
        self._match_data: dict[int, LiveMatch] = {}
        self._workers: dict[str, WorkerInfo] = {}
        self._scheduler_running: bool = False
        self._provider_healthy: bool = False
        self._last_heartbeat: datetime | None = None
        self._start_time: datetime = datetime.now(UTC)
        self._events_published: int = 0

    # ── Match State ──────────────────────────────────────────────────

    async def update_match_state(self, fixture_id: int, state: MatchState) -> None:
        """Update the state of a match."""
        old_state = self._match_states.get(fixture_id)
        self._match_states[fixture_id] = state
        if old_state != state:
            logger.info(f"Fixture {fixture_id}: {old_state} → {state}")

    async def get_match_state(self, fixture_id: int) -> MatchState | None:
        """Get the current state of a match."""
        return self._match_states.get(fixture_id)

    async def store_match(self, match: LiveMatch) -> None:
        """Store match data."""
        self._match_data[match.fixture_id] = match
        self._match_states[match.fixture_id] = match.state

    async def remove_match(self, fixture_id: int) -> None:
        """Remove a match from tracking."""
        self._match_data.pop(fixture_id, None)
        self._match_states.pop(fixture_id, None)
        logger.debug(f"Removed fixture {fixture_id} from tracking")

    async def get_active_matches(self) -> dict[int, MatchState]:
        """Get all active match states (excludes FINISHED/CANCELLED)."""
        terminal = {MatchState.FINISHED, MatchState.CANCELLED, MatchState.POSTPONED}
        return {
            fid: state
            for fid, state in self._match_states.items()
            if state not in terminal
        }

    async def get_match_data(self, fixture_id: int) -> LiveMatch | None:
        """Get stored match data."""
        return self._match_data.get(fixture_id)

    # ── Worker State ─────────────────────────────────────────────────

    async def register_worker(self, worker_id: str) -> None:
        """Register a new worker."""
        self._workers[worker_id] = WorkerInfo(worker_id=worker_id)
        logger.debug(f"Registered worker: {worker_id}")

    async def update_worker_status(
        self, worker_id: str, status: WorkerStatus, fixture_id: int | None = None
    ) -> None:
        """Update worker status."""
        if worker_id in self._workers:
            worker = self._workers[worker_id]
            worker.status = status
            worker.current_fixture_id = fixture_id
            worker.last_active = datetime.now(UTC)
            if status == WorkerStatus.PROCESSING:
                worker.processed_count += 1
            elif status == WorkerStatus.ERROR:
                worker.error_count += 1

    async def get_worker(self, worker_id: str) -> WorkerInfo | None:
        """Get worker info."""
        return self._workers.get(worker_id)

    async def get_all_workers(self) -> dict[str, WorkerInfo]:
        """Get all worker info."""
        return dict(self._workers)

    async def get_idle_workers(self) -> list[str]:
        """Get IDs of idle workers."""
        return [
            wid for wid, w in self._workers.items() if w.status == WorkerStatus.IDLE
        ]

    # ── Engine State ─────────────────────────────────────────────────

    def set_scheduler_running(self, running: bool) -> None:
        """Set scheduler status."""
        self._scheduler_running = running

    def set_provider_healthy(self, healthy: bool) -> None:
        """Set provider health status."""
        self._provider_healthy = healthy

    def record_heartbeat(self) -> None:
        """Record a heartbeat."""
        self._last_heartbeat = datetime.now(UTC)

    def increment_events_published(self) -> None:
        """Increment the events published counter."""
        self._events_published += 1

    def get_uptime(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now(UTC) - self._start_time).total_seconds()

    # ── Heartbeat ────────────────────────────────────────────────────

    def get_heartbeat(self) -> HeartbeatInfo:
        """Get current heartbeat information."""
        active_workers = [
            w for w in self._workers.values() if w.status != WorkerStatus.STOPPED
        ]
        return HeartbeatInfo(
            timestamp=datetime.now(UTC),
            scheduler_running=self._scheduler_running,
            workers_healthy=len(
                [w for w in active_workers if w.status != WorkerStatus.ERROR]
            ),
            workers_total=len(self._workers),
            provider_healthy=self._provider_healthy,
            queue_size=0,  # Set by the engine
            uptime_seconds=self.get_uptime(),
        )

    def get_metrics_snapshot(self) -> dict[str, object]:
        """Get a snapshot of all metrics."""
        return {
            "active_matches": len(self._match_states),
            "workers_active": len(
                [
                    w
                    for w in self._workers.values()
                    if w.status == WorkerStatus.PROCESSING
                ]
            ),
            "workers_total": len(self._workers),
            "events_published": self._events_published,
            "scheduler_running": self._scheduler_running,
            "provider_healthy": self._provider_healthy,
            "last_heartbeat": self._last_heartbeat.isoformat()
            if self._last_heartbeat
            else None,
            "uptime_seconds": self.get_uptime(),
        }
