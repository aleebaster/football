"""Scheduler module for periodic data synchronization.

Uses APScheduler AsyncIOScheduler for proper async job scheduling.
"""

from collections.abc import Callable, Coroutine
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.logging import get_logger

logger = get_logger(__name__)


class ProviderScheduler:
    """Scheduler for periodic provider data synchronization.

    Uses APScheduler AsyncIOScheduler as the primary scheduling mechanism.
    Supports adding/removing jobs, starting/stopping the scheduler.
    """

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._running = False

    def add_job(
        self,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        interval: float,
        **kwargs: Any,
    ) -> None:
        """Add a periodic job to the scheduler.

        Args:
            name: Unique job name.
            func: Async function to execute.
            interval: Interval in seconds between executions.
            **kwargs: Additional arguments passed to the function.
        """
        trigger = IntervalTrigger(seconds=interval)
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=name,
            name=name,
            kwargs=kwargs,
            replace_existing=True,
        )
        self._jobs[name] = {
            "func": func,
            "interval": interval,
            "kwargs": kwargs,
        }
        logger.info(f"Scheduled job: {name} (interval={interval}s)")

    def remove_job(self, name: str) -> None:
        """Remove a job from the scheduler.

        Args:
            name: Job name to remove.
        """
        try:
            self._scheduler.remove_job(name)
        except Exception:
            pass
        self._jobs.pop(name, None)
        logger.info(f"Removed job: {name}")

    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        self._scheduler.start()
        self._running = True
        logger.info(f"Scheduler started with {len(self._jobs)} jobs")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        self._running = False
        logger.info("Scheduler stopped")

    @property
    def jobs(self) -> list[str]:
        """Get list of scheduled job names."""
        return list(self._jobs.keys())

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running
