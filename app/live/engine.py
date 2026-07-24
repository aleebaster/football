"""Live Engine — main entry point for the Live Engine.

Coordinates: Scheduler, Worker Pool, Event Dispatcher, Publisher, State Registry.

Pipeline:
    Scheduler → Discovery → Queue → Worker → Provider → AI → Prediction → Signal → Publisher
"""

from __future__ import annotations

from app.live.dispatcher import EventDispatcher
from app.live.events import LiveEvent
from app.live.heartbeat import HeartbeatMonitor
from app.live.matcher import MatchDiscovery
from app.live.metrics import LiveMetricsCollector
from app.live.models import LiveMatch
from app.live.publisher import EventPublisher
from app.live.queue import MatchQueue
from app.live.registry import LiveComponentRegistry
from app.live.scheduler import LiveScheduler
from app.live.state import StateRegistry
from app.live.worker import LiveWorker
from app.logging import get_logger
from app.providers.manager import ProviderManager

logger = get_logger(__name__)


class LiveEngine:
    """Main entry point for the Live Engine.

    Usage:
        engine = LiveEngine(provider_manager)
        await engine.start()
        # ... application runs ...
        await engine.stop()

    The engine coordinates:
    - Scheduler: periodic discovery cycles
    - Workers: parallel match processing
    - Publisher: event broadcasting
    - State: match and worker state tracking
    - Heartbeat: health monitoring
    """

    def __init__(
        self,
        provider_manager: ProviderManager,
        num_workers: int = 3,
        discovery_interval: float = 60.0,
        heartbeat_interval: float = 30.0,
    ) -> None:
        # Core components
        self._provider_manager = provider_manager
        self._state_registry = StateRegistry()
        self._queue = MatchQueue()
        self._publisher = EventPublisher()

        # Discovery
        self._discovery = MatchDiscovery(provider_manager)

        # Workers — inject engines via DI (no service locator)
        from app.core.container import get_container

        container = get_container()
        self._workers = [
            LiveWorker(
                worker_id=f"worker_{i}",
                provider_manager=provider_manager,
                state_registry=self._state_registry,
                prediction_engine=container.prediction_engine,
                signal_engine=container.signal_engine,
            )
            for i in range(num_workers)
        ]

        # Dispatcher
        self._dispatcher = EventDispatcher(self._publisher)

        # Coordinator
        from app.live.coordinator import LiveCoordinator

        self._coordinator = LiveCoordinator(
            discovery=self._discovery,
            queue=self._queue,
            workers=self._workers,
            dispatcher=self._dispatcher,
            state_registry=self._state_registry,
        )

        # Scheduler
        self._scheduler = LiveScheduler(
            coordinator=self._coordinator,
            discovery_interval=discovery_interval,
        )

        # Heartbeat
        from app.providers.health import HealthChecker

        self._heartbeat = HeartbeatMonitor(
            state_registry=self._state_registry,
            workers=self._workers,
            health_checker=HealthChecker(providers=provider_manager._registry.values()),
            interval=heartbeat_interval,
        )

        # Metrics
        self._metrics = LiveMetricsCollector(self._state_registry)

        # Component registry
        self._registry = LiveComponentRegistry(
            state_registry=self._state_registry,
            queue=self._queue,
            publisher=self._publisher,
            workers=self._workers,
            metrics=self._metrics,
            heartbeat=self._heartbeat,
        )

        logger.info(
            f"Live Engine initialized ({num_workers} workers, "
            f"discovery_interval={discovery_interval}s)"
        )

    async def start(self) -> None:
        """Start the Live Engine."""
        await self._coordinator.start()
        await self._scheduler.start()
        await self._heartbeat.start()
        logger.info("Live Engine started")

    async def stop(self) -> None:
        """Stop the Live Engine."""
        await self._scheduler.stop()
        await self._heartbeat.stop()
        await self._coordinator.stop()
        logger.info("Live Engine stopped")

    async def process_match(self, match: LiveMatch) -> list[LiveEvent]:
        """Process a single match immediately (bypasses scheduler)."""
        return await self._coordinator.process_single(match)

    # ── Properties ───────────────────────────────────────────────────

    @property
    def publisher(self) -> EventPublisher:
        return self._publisher

    @property
    def state(self) -> StateRegistry:
        return self._state_registry

    @property
    def queue(self) -> MatchQueue:
        return self._queue

    @property
    def metrics(self) -> LiveMetricsCollector:
        return self._metrics

    @property
    def heartbeat(self) -> HeartbeatMonitor:
        return self._heartbeat

    @property
    def components(self) -> LiveComponentRegistry:
        return self._registry

    @property
    def is_running(self) -> bool:
        return self._scheduler.is_running

    def get_status(self) -> dict[str, object]:
        """Get full engine status."""
        return {
            "running": self.is_running,
            "queue_size": self._queue.size,
            "workers": len(self._workers),
            "busy_workers": len([w for w in self._workers if w.is_busy]),
            "events_published": self._publisher.published_count,
            "handlers": self._publisher.handler_count,
            **self._state_registry.get_metrics_snapshot(),
        }
