"""Backtesting Scheduler — manages scheduled backtest runs."""

from app.logging import get_logger

logger = get_logger(__name__)


class BacktestScheduler:
    """Manages scheduled backtest execution.

    Placeholder for future APScheduler integration.
    """

    def __init__(self) -> None:
        self._scheduled: dict[str, dict[str, object]] = {}

    def schedule(
        self,
        job_id: str,
        config: dict[str, object],
    ) -> None:
        """Schedule a backtest job.

        Args:
            job_id: Unique job identifier.
            config: Backtest configuration.
        """
        self._scheduled[job_id] = config
        logger.info(f"Scheduled backtest job: {job_id}")

    def cancel(self, job_id: str) -> bool:
        """Cancel a scheduled backtest job.

        Args:
            job_id: Job identifier.

        Returns:
            True if cancelled.
        """
        if job_id in self._scheduled:
            del self._scheduled[job_id]
            logger.info(f"Cancelled backtest job: {job_id}")
            return True
        return False

    def get_scheduled(self) -> dict[str, dict[str, object]]:
        """Get all scheduled jobs.

        Returns:
            Dictionary of scheduled jobs.
        """
        return dict(self._scheduled)

    def clear(self) -> None:
        """Clear all scheduled jobs."""
        self._scheduled.clear()
        logger.info("Cleared all scheduled backtest jobs")

    def __len__(self) -> int:
        return len(self._scheduled)
