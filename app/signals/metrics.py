"""Metrics — monitors Signal Engine performance."""

from datetime import UTC, datetime

from app.logging import get_logger
from app.signals.models import SignalMetrics

logger = get_logger(__name__)


class MetricsCollector:
    """Collects and tracks Signal Engine metrics."""

    def __init__(self) -> None:
        self._start_time = datetime.now(UTC)
        self._metrics = SignalMetrics()

    def record_processed(self, count: int = 1) -> None:
        """Record signals processed."""
        self._metrics.total_processed += count

    def record_generated(self, count: int = 1) -> None:
        """Record signals generated."""
        self._metrics.total_generated += count

    def record_filtered(self, count: int = 1) -> None:
        """Record signals filtered out."""
        self._metrics.total_filtered += count

    def record_duplicate(self, count: int = 1) -> None:
        """Record duplicate signals detected."""
        self._metrics.total_duplicates += count

    def record_cooldown(self, count: int = 1) -> None:
        """Record signals blocked by cooldown."""
        self._metrics.total_cooldown += count

    def record_processing_time(self, ms: float) -> None:
        """Record processing time for a batch."""
        total = self._metrics.avg_processing_time_ms * (
            self._metrics.total_processed - 1
        )
        total += ms
        self._metrics.avg_processing_time_ms = total / max(
            self._metrics.total_processed, 1
        )
        self._metrics.last_processed_at = datetime.now(UTC)

    def get_metrics(self) -> SignalMetrics:
        """Get current metrics."""
        uptime = (datetime.now(UTC) - self._start_time).total_seconds()
        self._metrics.uptime_seconds = round(uptime, 2)
        return self._metrics.model_copy()

    def reset(self) -> None:
        """Reset all metrics."""
        self._start_time = datetime.now(UTC)
        self._metrics = SignalMetrics()
        logger.info("Metrics reset")
