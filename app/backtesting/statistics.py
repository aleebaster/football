"""Backtesting Statistics — provides statistical analysis of backtest data.

Delegates to BacktestMetricsCalculator for core calculations to avoid duplication.
"""

from collections import defaultdict

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
        # Use metrics calculator's calibration buckets for consistency
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
        buckets: dict[str, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            bucket_idx = int(r.risk_score / bucket_size)
            bucket_key = (
                f"{bucket_idx * bucket_size:.1f}-{(bucket_idx + 1) * bucket_size:.1f}"
            )
            buckets[bucket_key].append(r)

        stats: dict[str, dict[str, object]] = {}
        for bucket_key, bucket_results in buckets.items():
            total = len(bucket_results)
            correct = sum(1 for r in bucket_results if r.is_correct)
            stats[bucket_key] = {
                "total": total,
                "correct": correct,
                "win_rate": correct / total if total > 0 else 0.0,
            }
        return stats

    def calculate_by_predictor(
        self, results: list[EvaluationResult]
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by model version (predictor)."""
        by_version: dict[str, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            by_version[r.model_version].append(r)

        stats: dict[str, dict[str, object]] = {}
        for version, version_results in by_version.items():
            total = len(version_results)
            correct = sum(1 for r in version_results if r.is_correct)
            stats[version] = {
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
