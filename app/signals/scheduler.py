"""Scheduler — manages scheduled signal processing tasks."""

from app.logging import get_logger

logger = get_logger(__name__)


class SignalScheduler:
    """Manages scheduled signal processing tasks.

    Provides configuration for when signals should be processed.
    Actual scheduling is handled by the application's scheduler integration.
    """

    def __init__(self) -> None:
        self._intervals: dict[str, int] = {
            "pre_match": 300,  # 5 minutes before match
            "live": 60,  # Every minute during live
            "post_match": 600,  # 10 minutes after match
            "daily_cleanup": 86400,  # Daily
        }
        self._enabled = True

    def get_interval(self, task: str) -> int:
        """Get interval for a task in seconds.

        Args:
            task: Task name.

        Returns:
            Interval in seconds.
        """
        return self._intervals.get(task, 300)

    def set_interval(self, task: str, interval: int) -> None:
        """Set interval for a task.

        Args:
            task: Task name.
            interval: Interval in seconds.
        """
        self._intervals[task] = interval
        logger.debug(f"Set interval for {task} to {interval}s")

    def enable(self) -> None:
        """Enable the scheduler."""
        self._enabled = True
        logger.info("Signal scheduler enabled")

    def disable(self) -> None:
        """Disable the scheduler."""
        self._enabled = False
        logger.info("Signal scheduler disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if scheduler is enabled."""
        return self._enabled

    def get_all_tasks(self) -> dict[str, int]:
        """Get all scheduled tasks and their intervals."""
        return dict(self._intervals)
