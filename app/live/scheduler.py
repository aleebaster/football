"""Live Engine — Scheduler using the existing APScheduler integration.

Uses the already-implemented ProviderScheduler pattern.
NOT creating a new scheduler — reusing APScheduler AsyncIOScheduler.
"""

from __future__ import annotations

import uuid

from app.live.coordinator import LiveCoordinator
from app.live.logging_context import LogContext, Timer, log_with_context
from app.live.recovery import SchedulerRecovery
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
        recovery: SchedulerRecovery | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._discovery_interval = discovery_interval
        self._scheduler = ProviderScheduler()
        self._running = False
        self._recovery = recovery or SchedulerRecovery()
        self._cycle_count = 0

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
        """Run a single coordinator cycle with recovery."""
        cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
        self._cycle_count += 1

        ctx = LogContext(scheduler_cycle=cycle_id)

        with ctx:
            with Timer() as timer:
                try:
                    await self._coordinator.run_cycle()
                    self._recovery.record_success()

                    log_with_context(
                        logger,
                        "info",
                        f"Scheduler cycle {cycle_id} completed in {timer.elapsed_ms:.1f}ms",
                    )

                except Exception as e:
                    self._recovery.record_failure()
                    log_with_context(
                        logger, "warning", f"Scheduler cycle {cycle_id} failed: {e}"
                    )

                    # Attempt recovery
                    async def restart_fn() -> bool:
                        logger.info(f"Restarting coordinator for cycle {cycle_id}")
                        return True

                    await self._recovery.recover(f"scheduler_{cycle_id}", restart_fn)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def jobs(self) -> list[str]:
        return self._scheduler.jobs
