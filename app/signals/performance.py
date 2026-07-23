"""Performance — tracks performance statistics by market type."""

from app.logging import get_logger
from app.prediction.models import PredictionMarket
from app.signals.history import SignalHistoryStore
from app.signals.models import PerformanceStatistics

logger = get_logger(__name__)


class PerformanceEngine:
    """Calculates performance statistics by market type."""

    def __init__(self, history: SignalHistoryStore | None = None) -> None:
        self._history = history

    async def calculate_performance(
        self,
        market: PredictionMarket | None = None,
    ) -> PerformanceStatistics | list[PerformanceStatistics]:
        """Calculate performance statistics.

        Args:
            market: Optional market to filter by. If None, returns all.

        Returns:
            Performance statistics for the market or all markets.
        """
        if self._history is None:
            if market:
                return PerformanceStatistics(market=market)
            return [PerformanceStatistics(market=m) for m in PredictionMarket]

        if market:
            return await self._calculate_for_market(market)
        return await self._calculate_all_markets()

    async def _calculate_for_market(
        self,
        market: PredictionMarket,
    ) -> PerformanceStatistics:
        """Calculate performance for a specific market."""
        if self._history is None:
            return PerformanceStatistics(market=market)

        all_records = await self._history.get_all_records()
        records = [r for r in all_records if r.signal.market == market]

        completed = [r for r in records if r.is_correct is not None]
        if not completed:
            return PerformanceStatistics(market=market)

        total = len(completed)
        wins = sum(1 for r in completed if r.is_correct)
        total_roi = sum(r.roi for r in completed)
        total_conf = sum(r.signal.confidence for r in completed)
        total_edge = sum(r.edge for r in completed)

        return PerformanceStatistics(
            market=market,
            total_signals=total,
            win_rate=round(wins / total, 4),
            roi=round(total_roi / total, 4),
            average_confidence=round(total_conf / total, 4),
            average_edge=round(total_edge / total, 4),
        )

    async def _calculate_all_markets(self) -> list[PerformanceStatistics]:
        """Calculate performance for all markets."""
        results = []
        for market in PredictionMarket:
            stats = await self._calculate_for_market(market)
            if stats.total_signals > 0:
                results.append(stats)
        results.sort(key=lambda s: s.roi, reverse=True)
        return results

    async def get_best_performing_market(self) -> PerformanceStatistics | None:
        """Get the best performing market by ROI.

        Returns:
            Best performing market statistics or None.
        """
        all_stats = await self._calculate_all_markets()
        return all_stats[0] if all_stats else None

    async def get_worst_performing_market(self) -> PerformanceStatistics | None:
        """Get the worst performing market by ROI.

        Returns:
            Worst performing market statistics or None.
        """
        all_stats = await self._calculate_all_markets()
        return all_stats[-1] if all_stats else None
