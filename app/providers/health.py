"""Health check module for providers."""

import asyncio
import time

from app.logging import get_logger
from app.providers.base import BaseProvider
from app.providers.models import ProviderStatus

logger = get_logger(__name__)


class HealthChecker:
    """Periodic health checker for all providers."""

    def __init__(
        self, providers: list[BaseProvider], check_interval: float = 60.0
    ) -> None:
        self._providers = providers
        self._check_interval = check_interval
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def check_provider(self, provider: BaseProvider) -> ProviderStatus:
        try:
            start = time.perf_counter()
            status = await provider.check_health()
            elapsed = time.perf_counter() - start
            provider.health_info.record_success(elapsed)
            logger.debug(
                f"Health check {provider.name}: {status.value} ({elapsed:.3f}s)"
            )
            return status
        except Exception as e:
            provider.health_info.record_failure()
            logger.warning(f"Health check failed for {provider.name}: {e}")
            return ProviderStatus.UNHEALTHY

    async def check_all(self) -> dict[str, ProviderStatus]:
        results: dict[str, ProviderStatus] = {}
        for provider in self._providers:
            results[provider.name] = await self.check_provider(provider)
        return results

    async def _loop(self) -> None:
        while self._running:
            await self.check_all()
            await asyncio.sleep(self._check_interval)

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())
            logger.info(f"Health checker started (interval={self._check_interval}s)")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("Health checker stopped")
