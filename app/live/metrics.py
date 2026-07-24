"""Live Engine — Metrics collector for monitoring the Live Engine."""

from __future__ import annotations

from datetime import UTC, datetime

from app.live.models import LiveMetrics
from app.live.state import StateRegistry
from app.logging import get_logger

logger = get_logger(__name__)


class LiveMetricsCollector:
    """Collects and reports Live Engine metrics."""

    def __init__(self, state_registry: StateRegistry) -> None:
        self._state_registry = state_registry
        self._start_time: datetime = datetime.now(UTC)
        self._prediction_times: list[float] = []
        self._signal_times: list[float] = []
        self._provider_latencies: list[float] = []

    def record_prediction_time(self, elapsed_ms: float) -> None:
        """Record prediction processing time."""
        self._prediction_times.append(elapsed_ms)
        if len(self._prediction_times) > 1000:
            self._prediction_times = self._prediction_times[-500:]

    def record_signal_time(self, elapsed_ms: float) -> None:
        """Record signal processing time."""
        self._signal_times.append(elapsed_ms)
        if len(self._signal_times) > 1000:
            self._signal_times = self._signal_times[-500:]

    def record_provider_latency(self, latency_ms: float) -> None:
        """Record provider response latency."""
        self._provider_latencies.append(latency_ms)
        if len(self._provider_latencies) > 1000:
            self._provider_latencies = self._provider_latencies[-500:]

    def get_metrics(self) -> LiveMetrics:
        """Get current metrics snapshot."""
        state = self._state_registry.get_metrics_snapshot()
        return LiveMetrics(
            active_matches=state.get("active_matches", 0),  # type: ignore[arg-type]
            workers_active=state.get("workers_active", 0),  # type: ignore[arg-type]
            workers_total=state.get("workers_total", 0),  # type: ignore[arg-type]
            events_published=state.get("events_published", 0),  # type: ignore[arg-type]
            avg_prediction_time_ms=self._avg(self._prediction_times),
            avg_signal_time_ms=self._avg(self._signal_times),
            provider_latency_ms=self._avg(self._provider_latencies),
            last_heartbeat=state.get("last_heartbeat"),  # type: ignore[arg-type]
            uptime_seconds=(datetime.now(UTC) - self._start_time).total_seconds(),
        )

    @staticmethod
    def _avg(values: list[float]) -> float:
        """Calculate average of a list of values."""
        return sum(values) / len(values) if values else 0.0
