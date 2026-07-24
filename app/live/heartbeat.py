"""Live Engine — Heartbeat monitor for health tracking.

Monitors worker health, provider health, and scheduler status.
"""

from __future__ import annotations

import asyncio

from app.live.models import HeartbeatInfo
from app.live.state import StateRegistry
from app.live.worker import LiveWorker
from app.logging import get_logger
from app.providers.health import HealthChecker

logger = get_logger(__name__)


class HeartbeatMonitor:
    """Periodic heartbeat monitor for the Live Engine.

    Tracks:
    - Worker health
    - Provider health
    - Scheduler status
    """

    def __init__(
        self,
        state_registry: StateRegistry,
        workers: list[LiveWorker] | None = None,
        health_checker: HealthChecker | None = None,
        interval: float = 30.0,
    ) -> None:
        self._state_registry = state_registry
        self._workers = workers or []
        self._health_checker = health_checker
        self._interval = interval
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the heartbeat monitor."""
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Heartbeat monitor started (interval={self._interval}s)")

    async def stop(self) -> None:
        """Stop the heartbeat monitor."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat monitor stopped")

    async def _loop(self) -> None:
        """Heartbeat loop."""
        while self._running:
            try:
                await self._tick()
            except Exception as e:
                logger.warning(f"Heartbeat tick failed: {e}")
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        """Perform a single heartbeat check."""
        self._state_registry.record_heartbeat()

        # Check provider health
        if self._health_checker:
            try:
                results = await self._health_checker.check_all()
                healthy = any(
                    status.value in ("healthy", "degraded")
                    for status in results.values()
                )
                self._state_registry.set_provider_healthy(healthy)
            except Exception as e:
                logger.debug(f"Provider health check failed: {e}")
                self._state_registry.set_provider_healthy(False)

        # Log heartbeat
        heartbeat = self._state_registry.get_heartbeat()
        logger.debug(
            f"Heartbeat: workers={heartbeat.workers_healthy}/{heartbeat.workers_total}, "
            f"provider={'ok' if heartbeat.provider_healthy else 'fail'}, "
            f"scheduler={'running' if heartbeat.scheduler_running else 'stopped'}"
        )

    def get_info(self) -> HeartbeatInfo:
        """Get current heartbeat info."""
        return self._state_registry.get_heartbeat()
