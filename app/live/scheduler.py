"""Live Engine — Scheduler using the existing APScheduler integration.

Uses the already-implemented ProviderScheduler pattern.
NOT creating a new scheduler — reusing APScheduler AsyncIOScheduler.
"""

from __future__ import annotations

from app.live.coordinator import LiveCoordinator
from app.logging import get_logger
from app.providers.scheduler import ProviderScheduler

logger = get_logger(__name__)


class LiveScheduler:
    """Scheduler for the Live Engine cycle.

    Uses the existing ProviderScheduler (APScheduler) to run
    periodic discovery and processing cycles.
    """

    def __init__(
        self,
        coordinator: LiveCoordinator,
        discovery_interval: float = 60.0,
    ) -> None:
        self._coordinator = coordinator
        self._discovery_interval = discovery_interval
        self._scheduler = ProviderScheduler()
        self._running = False

    async def start(self) -> None:
        """Start the Live Scheduler."""
        if self._running:
            return

        self._scheduler.add_job(
            name="live_discovery_cycle",
            func=self._run_cycle,
            interval=self._discovery_interval,
        )
        self._scheduler.start()
        self._running = True
        logger.info(
            f"Live Scheduler started (discovery interval={self._discovery_interval}s)"
        )

    async def stop(self) -> None:
        """Stop the Live Scheduler."""
        if not self._running:
            return
        self._scheduler.stop()
        self._running = False
        logger.info("Live Scheduler stopped")

    async def _run_cycle(self) -> None:
        """Run a single coordinator cycle."""
        await self._coordinator.run_cycle()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def jobs(self) -> list[str]:
        return self._scheduler.jobs
