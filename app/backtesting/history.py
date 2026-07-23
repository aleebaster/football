"""Backtesting History — tracks backtest run history."""

from datetime import UTC, datetime

from app.backtesting.models import BacktestResult
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestHistory:
    """Tracks history of backtest runs."""

    def __init__(self) -> None:
        self._runs: list[dict[str, object]] = []

    async def record_run(self, result: BacktestResult) -> None:
        """Record a completed backtest run.

        Args:
            result: Completed backtest result.
        """
        record: dict[str, object] = {
            "id": result.id,
            "status": result.status.value,
            "ai_version": result.ai_version,
            "total_evaluations": len(result.evaluations),
            "win_rate": result.metrics.win_rate,
            "roi": result.metrics.roi,
            "started_at": result.started_at.isoformat(),
            "completed_at": (
                result.completed_at.isoformat() if result.completed_at else None
            ),
            "duration_seconds": result.duration_seconds,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        self._runs.append(record)
        logger.debug(f"Recorded backtest run {result.id}")

    async def get_runs(self) -> list[dict[str, object]]:
        """Get all recorded backtest runs.

        Returns:
            List of run records.
        """
        return list(self._runs)

    async def get_latest(self) -> dict[str, object] | None:
        """Get the most recent backtest run.

        Returns:
            Latest run record or None.
        """
        return self._runs[-1] if self._runs else None

    async def clear(self) -> None:
        """Clear all history records."""
        self._runs.clear()
        logger.info("Cleared backtest history")

    def __len__(self) -> int:
        return len(self._runs)
