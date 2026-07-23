"""Backtesting Statistics — provides statistical analysis of backtest data."""

from collections import defaultdict

from app.backtesting.models import EvaluationResult
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestStatistics:
    """Provides statistical analysis of backtest evaluation data."""

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
            }
        return stats

    def calculate_by_confidence_bucket(
        self, results: list[EvaluationResult], bucket_size: float = 0.1
    ) -> dict[str, dict[str, object]]:
        """Calculate statistics grouped by confidence buckets.

        Args:
            results: Evaluation results.
            bucket_size: Size of each confidence bucket.

        Returns:
            Dictionary of bucket statistics.
        """
        buckets: dict[str, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            bucket_idx = int(r.confidence / bucket_size)
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
