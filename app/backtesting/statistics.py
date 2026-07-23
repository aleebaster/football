"""Backtesting Statistics — provides statistical analysis of backtest data.

Delegates to BacktestMetricsCalculator for core calculations to avoid duplication.
"""

from collections import defaultdict
from collections.abc import Callable

from app.backtesting.metrics import BacktestMetricsCalculator
from app.backtesting.models import EvaluationResult
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestStatistics:
    """Provides statistical analysis of backtest evaluation data.

    Delegates core bucketing to BacktestMetricsCalculator where possible.
    """

    def __init__(
        self, metrics_calculator: BacktestMetricsCalculator | None = None
    ) -> None:
        """Initialize statistics engine.

        Args:
            metrics_calculator: Shared metrics calculator instance.
                               Creates a new one if None (default).
        """
        self._metrics = metrics_calculator or BacktestMetricsCalculator()

    def calculate_by_league(
        self, results: list[EvaluationResult], league_map: dict[int, str] | None = None
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by league.

        Args:
            results: Evaluation results.
            league_map: Optional mapping of fixture_id to league name.

        Returns:
            Dictionary of league statistics.
        """
        by_league: dict[str, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            league = "unknown"
            if league_map and r.fixture_id in league_map:
                league = league_map[r.fixture_id]
            by_league[league].append(r)

        stats: dict[str, dict[str, object]] = {}
        for league, league_results in by_league.items():
            total = len(league_results)
            correct = sum(1 for r in league_results if r.is_correct)
            total_stake = sum(r.stake for r in league_results)
            total_pnl = sum(r.pnl for r in league_results)
            stats[league] = {
                "total": total,
                "correct": correct,
                "win_rate": correct / total if total > 0 else 0.0,
                "avg_odds": sum(r.odds for r in league_results) / total
                if total > 0
                else 1.0,
                "avg_confidence": sum(r.confidence for r in league_results) / total
                if total > 0
                else 0.0,
                "roi": total_pnl / total_stake if total_stake > 0 else 0.0,
            }
        return stats

    def calculate_by_confidence_bucket(
        self, results: list[EvaluationResult], bucket_size: float = 0.1
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by confidence buckets.

        Delegates bucketing to the metrics calculator's calibration buckets.
        """
        cal_buckets = self._metrics.calculate_calibration_buckets(results)

        stats: dict[str, dict[str, object]] = {}
        for bucket in cal_buckets:
            bucket_key = f"{bucket.lower:.1f}-{bucket.upper:.1f}"
            stats[bucket_key] = {
                "total": bucket.count,
                "correct": bucket.correct,
                "win_rate": bucket.observed_frequency,
                "expected_frequency": bucket.expected_frequency,
                "gap": bucket.gap,
            }
        return stats

    def calculate_by_risk_bucket(
        self, results: list[EvaluationResult], bucket_size: float = 0.1
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by risk score buckets."""

        def _risk_key(r: EvaluationResult) -> str:
            idx = int(r.risk_score / bucket_size)
            return f"{idx * bucket_size:.1f}-{(idx + 1) * bucket_size:.1f}"

        return self._group_and_summarize(results, _risk_key)

    def calculate_by_predictor(
        self, results: list[EvaluationResult]
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by model version (predictor)."""
        return self._group_and_summarize(results, lambda r: r.model_version)

    @staticmethod
    def _group_and_summarize(
        results: list[EvaluationResult],
        key_fn: Callable[[EvaluationResult], str],
    ) -> dict[str, dict[str, object]]:
        """Group results by key and compute win_rate summary."""
        grouped: dict[str, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            grouped[key_fn(r)].append(r)

        stats: dict[str, dict[str, object]] = {}
        for key, group in grouped.items():
            total = len(group)
            correct = sum(1 for r in group if r.is_correct)
            stats[key] = {
                "total": total,
                "correct": correct,
                "win_rate": correct / total if total > 0 else 0.0,
            }
        return stats

    def calculate_by_market(
        self, results: list[EvaluationResult]
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by market type.

        Delegates to metrics calculator's market breakdown.
        """
        breakdowns = self._metrics.calculate_market_breakdown(results)
        stats: dict[str, dict[str, object]] = {}
        for mb in breakdowns:
            stats[mb.market.value] = {
                "total": mb.total,
                "correct": mb.correct,
                "win_rate": mb.win_rate,
                "roi": mb.roi,
                "avg_odds": mb.average_odds,
                "avg_confidence": mb.average_confidence,
            }
        return stats

    def calculate_by_signal(
        self, results: list[EvaluationResult]
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by signal presence.

        Delegates to metrics calculator's signal statistics.
        """
        signal_stats = self._metrics.calculate_signal_statistics(results)
        stats: dict[str, dict[str, object]] = {}
        for ss in signal_stats:
            stats[ss.signal_type] = {
                "total": ss.total_signals,
                "correct": ss.winning_signals,
                "win_rate": ss.win_rate,
                "roi": ss.roi,
                "avg_confidence": ss.average_confidence,
            }
        return stats
