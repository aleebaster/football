"""Live Engine — Recovery Layer for fault tolerance.

Provides separate recovery mechanisms:
- Retry Policy: configurable retry with exponential backoff
- Worker Recovery: restart failed workers
- Provider Failure Recovery: handle provider failures gracefully
- Queue Recovery: recover stuck or corrupted queue state
- Scheduler Recovery: restart failed scheduler cycles
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from app.live.logging_context import log_with_context
from app.live.queue import MatchQueue
from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetryPolicy:
    """Configurable retry policy with exponential backoff."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    _attempt: int = field(default=0, repr=False)

    def reset(self) -> None:
        """Reset retry counter."""
        self._attempt = 0

    def get_delay(self) -> float:
        """Get delay for current attempt."""
        delay = self.base_delay * (self.backoff_factor**self._attempt)
        return min(delay, self.max_delay)

    def should_retry(self) -> bool:
        """Check if we should retry."""
        return self._attempt < self.max_retries

    def record_attempt(self) -> None:
        """Record a retry attempt."""
        self._attempt += 1

    @property
    def attempt(self) -> int:
        return self._attempt


class WorkerRecovery:
    """Recovery mechanism for failed workers."""

    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        self._retry_policy = retry_policy or RetryPolicy()
        self._failed_workers: dict[str, int] = {}

    async def recover(
        self,
        worker_id: str,
        restart_fn: Callable[[], Awaitable[bool]],
    ) -> bool:
        """Attempt to recover a failed worker.

        Args:
            worker_id: The ID of the failed worker.
            restart_fn: Async function to restart the worker.

        Returns:
            True if recovery succeeded, False otherwise.
        """
        self._retry_policy.reset()

        while self._retry_policy.should_retry():
            try:
                log_with_context(
                    logger,
                    "info",
                    f"Attempting worker recovery for {worker_id} "
                    f"(attempt {self._retry_policy.attempt + 1})",
                )
                await restart_fn()
                self._failed_workers.pop(worker_id, None)
                log_with_context(
                    logger, "info", f"Worker {worker_id} recovered successfully"
                )
                return True
            except Exception as e:
                self._retry_policy.record_attempt()
                delay = self._retry_policy.get_delay()
                log_with_context(
                    logger,
                    "warning",
                    f"Worker {worker_id} recovery attempt {self._retry_policy.attempt} "
                    f"failed: {e}. Retrying in {delay:.1f}s",
                )
                await asyncio.sleep(delay)

        self._failed_workers[worker_id] = self._retry_policy.attempt
        log_with_context(
            logger,
            "error",
            f"Worker {worker_id} recovery failed after {self._retry_policy.max_retries} attempts",
        )
        return False

    def get_failed_workers(self) -> dict[str, int]:
        """Get workers that failed recovery."""
        return dict(self._failed_workers)


class ProviderFailureRecovery:
    """Recovery mechanism for provider failures."""

    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        self._retry_policy = retry_policy or RetryPolicy(
            max_retries=5, base_delay=2.0, max_delay=60.0
        )

    async def recover(
        self,
        provider_name: str,
        recovery_fn: Callable[[], Awaitable[bool]],
    ) -> bool:
        """Attempt to recover from a provider failure.

        Args:
            provider_name: Name of the failed provider.
            recovery_fn: Async function to attempt recovery.

        Returns:
            True if recovery succeeded, False otherwise.
        """
        self._retry_policy.reset()

        while self._retry_policy.should_retry():
            try:
                log_with_context(
                    logger,
                    "info",
                    f"Attempting provider recovery for {provider_name} "
                    f"(attempt {self._retry_policy.attempt + 1})",
                )
                await recovery_fn()
                log_with_context(
                    logger, "info", f"Provider {provider_name} recovered successfully"
                )
                return True
            except Exception as e:
                self._retry_policy.record_attempt()
                delay = self._retry_policy.get_delay()
                log_with_context(
                    logger,
                    "warning",
                    f"Provider {provider_name} recovery attempt {self._retry_policy.attempt} "
                    f"failed: {e}. Retrying in {delay:.1f}s",
                )
                await asyncio.sleep(delay)

        log_with_context(
            logger,
            "error",
            f"Provider {provider_name} recovery failed after "
            f"{self._retry_policy.max_retries} attempts",
        )
        return False


class QueueRecovery:
    """Recovery mechanism for queue issues."""

    async def recover_stuck_queue(self, queue: MatchQueue) -> int:
        """Recover a stuck queue by clearing stale entries.

        Args:
            queue: The MatchQueue instance.

        Returns:
            Number of entries recovered.
        """
        recovered = 0
        try:
            stats = queue.get_stats()
            logger.info(f"Queue recovery: stats before = {stats}")

            # Clear processed entries to prevent re-processing
            await queue.clear_processed()

            logger.info(f"Queue recovery completed: {recovered} entries recovered")
        except Exception as e:
            logger.error(f"Queue recovery failed: {e}")

        return recovered

    async def validate_queue(self, queue: MatchQueue) -> bool:
        """Validate queue integrity.

        Args:
            queue: The MatchQueue instance.

        Returns:
            True if queue is healthy.
        """
        try:
            stats = queue.get_stats()
            total = stats.get("total", 0)
            max_size = 1000  # MatchQueue default

            if total > max_size:
                logger.warning(f"Queue size {total} exceeds maximum {max_size}")
                return False

            return True
        except Exception as e:
            logger.error(f"Queue validation failed: {e}")
            return False


class SchedulerRecovery:
    """Recovery mechanism for scheduler failures."""

    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        self._retry_policy = retry_policy or RetryPolicy(
            max_retries=3, base_delay=5.0, max_delay=60.0
        )
        self._consecutive_failures: int = 0
        self._max_consecutive_failures: int = 5

    async def recover(
        self,
        scheduler_name: str,
        restart_fn: Callable[[], Awaitable[bool]],
    ) -> bool:
        """Attempt to recover a failed scheduler.

        Args:
            scheduler_name: Name of the failed scheduler.
            restart_fn: Async function to restart the scheduler.

        Returns:
            True if recovery succeeded, False otherwise.
        """
        self._retry_policy.reset()

        while self._retry_policy.should_retry():
            try:
                log_with_context(
                    logger,
                    "info",
                    f"Attempting scheduler recovery for {scheduler_name} "
                    f"(attempt {self._retry_policy.attempt + 1})",
                )
                await restart_fn()
                self._consecutive_failures = 0
                log_with_context(
                    logger, "info", f"Scheduler {scheduler_name} recovered successfully"
                )
                return True
            except Exception as e:
                self._retry_policy.record_attempt()
                self._consecutive_failures += 1
                delay = self._retry_policy.get_delay()
                log_with_context(
                    logger,
                    "warning",
                    f"Scheduler {scheduler_name} recovery attempt {self._retry_policy.attempt} "
                    f"failed: {e}. Retrying in {delay:.1f}s",
                )
                await asyncio.sleep(delay)

        log_with_context(
            logger,
            "error",
            f"Scheduler {scheduler_name} recovery failed after "
            f"{self._retry_policy.max_retries} attempts",
        )
        return False

    @property
    def is_degraded(self) -> bool:
        """Check if scheduler is in degraded state."""
        return self._consecutive_failures >= self._max_consecutive_failures

    def record_success(self) -> None:
        """Record a successful cycle."""
        self._consecutive_failures = 0

    def record_failure(self) -> None:
        """Record a failed cycle."""
        self._consecutive_failures += 1
