"""ROI — tracks return on investment for signals."""

from app.logging import get_logger
from app.prediction.models import PredictionMarket
from app.signals.history import SignalHistoryStore
from app.signals.models import ROIStatistics

logger = get_logger(__name__)


class ROIEngine:
    """Calculates ROI and yield statistics."""

    def __init__(self, history: SignalHistoryStore | None = None) -> None:
        self._history = history

    async def calculate_roi(
        self,
        signal_ids: list[str] | None = None,
    ) -> ROIStatistics:
        """Calculate comprehensive ROI statistics.

        Args:
            signal_ids: Optional list of signal IDs to filter by.

        Returns:
            ROI statistics.
        """
        if self._history is None:
            return ROIStatistics()

        all_records = []
        if signal_ids is not None:
            all_records = await self._history.get_records_by_ids(signal_ids)
        else:
            all_records = await self._history.get_all_records()

        completed = [r for r in all_records if r.is_correct is not None]
        if not completed:
            return ROIStatistics()

        total = len(completed)
        wins = sum(1 for r in completed if r.is_correct)
        losses = total - wins

        total_roi = sum(r.roi for r in completed)
        avg_roi = total_roi / total if total > 0 else 0.0

        total_odds = sum(r.signal.odds for r in completed if r.signal.odds > 0)
        avg_odds = total_odds / total if total > 0 else 1.0

        total_conf = sum(r.signal.confidence for r in completed)
        avg_conf = total_conf / total if total > 0 else 0.0

        total_risk = sum(r.signal.risk_score for r in completed)
        avg_risk = total_risk / total if total > 0 else 0.0

        total_edge = sum(r.edge for r in completed)
        avg_edge = total_edge / total if total > 0 else 0.0

        win_rate = wins / total if total > 0 else 0.0
        yield_pct = avg_roi * 100

        return ROIStatistics(
            total_signals=total,
            winning_signals=wins,
            losing_signals=losses,
            roi=round(avg_roi, 4),
            yield_pct=round(yield_pct, 2),
            win_rate=round(win_rate, 4),
            average_odds=round(avg_odds, 2),
            average_confidence=round(avg_conf, 4),
            average_risk=round(avg_risk, 4),
            average_edge=round(avg_edge, 4),
            signal_accuracy=round(win_rate, 4),
        )

    async def calculate_market_roi(
        self,
        market: PredictionMarket,
    ) -> ROIStatistics:
        """Calculate ROI for a specific market.

        Args:
            market: Market type to filter by.

        Returns:
            ROI statistics for the market.
        """
        if self._history is None:
            return ROIStatistics()

        all_records = await self._history.get_all_records()
        market_signals = [r.signal_id for r in all_records if r.signal.market == market]
        return await self.calculate_roi(market_signals)
