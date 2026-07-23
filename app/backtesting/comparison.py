"""Backtesting Comparison — compares backtest results across versions."""

from app.backtesting.models import (
    BacktestResult,
    ComparisonResult,
)
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestComparison:
    """Compares backtest results across different versions or configurations."""

    def compare(
        self,
        result_a: BacktestResult,
        result_b: BacktestResult,
    ) -> ComparisonResult:
        """Compare two backtest results.

        Args:
            result_a: First backtest result (baseline).
            result_b: Second backtest result (comparison).

        Returns:
            ComparisonResult with improvements and regressions.
        """
        metrics_a = result_a.metrics
        metrics_b = result_b.metrics

        improvements: dict[str, float] = {}
        regressions: dict[str, float] = {}

        # Compare key metrics
        comparisons = {
            "win_rate": (metrics_a.win_rate, metrics_b.win_rate, True),
            "roi": (metrics_a.roi, metrics_b.roi, True),
            "brier_score": (metrics_a.brier_score, metrics_b.brier_score, False),
            "log_loss": (metrics_a.log_loss, metrics_b.log_loss, False),
            "accuracy": (metrics_a.accuracy, metrics_b.accuracy, True),
            "calibration_error": (
                metrics_a.calibration_error,
                metrics_b.calibration_error,
                False,
            ),
            "f1_score": (metrics_a.f1_score, metrics_b.f1_score, True),
            "average_ev": (metrics_a.average_ev, metrics_b.average_ev, True),
        }

        for metric_name, (val_a, val_b, higher_is_better) in comparisons.items():
            if val_a == 0 and val_b == 0:
                continue

            if higher_is_better:
                diff = val_b - val_a
                pct = (diff / abs(val_a)) * 100 if val_a != 0 else 100.0
            else:
                diff = val_a - val_b  # Lower is better
                pct = (diff / abs(val_a)) * 100 if val_a != 0 else 100.0

            if diff > 0:
                improvements[metric_name] = round(pct, 2)
            elif diff < 0:
                regressions[metric_name] = round(pct, 2)

        # Generate summary
        summary = self._generate_summary(improvements, regressions)

        comparison = ComparisonResult(
            version_a=result_a.ai_version,
            version_b=result_b.ai_version,
            metrics_a=metrics_a,
            metrics_b=metrics_b,
            improvement=improvements,
            regressions=regressions,
            summary=summary,
        )

        logger.info(
            f"Comparison complete: {len(improvements)} improvements, "
            f"{len(regressions)} regressions"
        )
        return comparison

    def _generate_summary(
        self,
        improvements: dict[str, float],
        regressions: dict[str, float],
    ) -> str:
        """Generate a human-readable comparison summary."""
        parts = []

        if improvements:
            top = sorted(improvements.items(), key=lambda x: x[1], reverse=True)[:3]
            improvements_str = ", ".join(f"{k}: +{v:.1f}%" for k, v in top)
            parts.append(f"Improvements: {improvements_str}")

        if regressions:
            top = sorted(regressions.items(), key=lambda x: x[1], reverse=True)[:3]
            regressions_str = ", ".join(f"{k}: -{v:.1f}%" for k, v in top)
            parts.append(f"Regressions: {regressions_str}")

        if not parts:
            return "No significant differences detected."

        return "; ".join(parts)
