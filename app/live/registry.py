"""Live Engine — Component Registry for managing Live Engine components."""

from __future__ import annotations

from app.live.heartbeat import HeartbeatMonitor
from app.live.metrics import LiveMetricsCollector
from app.live.publisher import EventPublisher
from app.live.queue import MatchQueue
from app.live.state import StateRegistry
from app.live.worker import LiveWorker
from app.logging import get_logger

logger = get_logger(__name__)


class LiveComponentRegistry:
    """Registry for all Live Engine components.

    Central place to access all Live Engine sub-components.
    """

    def __init__(
        self,
        state_registry: StateRegistry,
        queue: MatchQueue,
        publisher: EventPublisher,
        workers: list[LiveWorker],
        metrics: LiveMetricsCollector,
        heartbeat: HeartbeatMonitor,
    ) -> None:
        self._state = state_registry
        self._queue = queue
        self._publisher = publisher
        self._workers = workers
        self._metrics = metrics
        self._heartbeat = heartbeat

    @property
    def state(self) -> StateRegistry:
        return self._state

    @property
    def queue(self) -> MatchQueue:
        return self._queue

    @property
    def publisher(self) -> EventPublisher:
        return self._publisher

    @property
    def workers(self) -> list[LiveWorker]:
        return self._workers

    @property
    def metrics(self) -> LiveMetricsCollector:
        return self._metrics

    @property
    def heartbeat(self) -> HeartbeatMonitor:
        return self._heartbeat

    def get_idle_worker_count(self) -> int:
        """Get number of idle workers."""
        return len([w for w in self._workers if not w.is_busy])

    def get_busy_worker_count(self) -> int:
        """Get number of busy workers."""
        return len([w for w in self._workers if w.is_busy])
