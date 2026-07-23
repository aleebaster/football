"""Backtesting Reporting — generates reports from backtest results."""

from app.backtesting.metrics import BacktestMetricsCalculator
from app.backtesting.models import (
    BacktestResult,
    BacktestSummary,
)
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestReporter:
    """Generates summary reports from backtest results.

    Supports: Summary, Per Market, Per Confidence Bucket, Per Risk Bucket,
    Per Predictor, Per Signal Generator.
    """

    def __init__(
        self, metrics_calculator: BacktestMetricsCalculator | None = None
    ) -> None:
        self._metrics_calculator = metrics_calculator or BacktestMetricsCalculator()

    async def generate(self, result: BacktestResult) -> BacktestSummary:
        """Generate a full summary report from backtest results."""
        if result.metrics.total_predictions == 0 and result.evaluations:
            result.metrics = await self._metrics_calculator.calculate(
                result.evaluations
            )

        market_breakdown = self._metrics_calculator.calculate_market_breakdown(
            result.evaluations
        )
        calibration_buckets = self._metrics_calculator.calculate_calibration_buckets(
            result.evaluations
        )
        prediction_statistics = (
            self._metrics_calculator.calculate_prediction_statistics(result.evaluations)
        )
        signal_statistics = self._metrics_calculator.calculate_signal_statistics(
            result.evaluations
        )

        summary = BacktestSummary(
            request=result.request,
            status=result.status,
            metrics=result.metrics,
            market_breakdown=market_breakdown,
            calibration_buckets=calibration_buckets,
            prediction_statistics=prediction_statistics,
            signal_statistics=signal_statistics,
            total_evaluations=len(result.evaluations),
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=result.duration_seconds,
        )

        result.summary = summary
        logger.info(
            f"Generated summary: {summary.total_evaluations} evaluations, "
            f"win_rate={result.metrics.win_rate:.2%}"
        )
        return summary

    def format_text_report(self, summary: BacktestSummary) -> str:
        """Format a summary as a readable text report."""
        m = summary.metrics
        lines = [
            "=" * 60,
            "BACKTEST REPORT",
            "=" * 60,
            f"Scope: {summary.request.scope.value}",
            f"Status: {summary.status.value}",
            f"Total Evaluations: {summary.total_evaluations}",
            f"Duration: {summary.duration_seconds:.1f}s",
            "",
            "--- KEY METRICS ---",
            f"Win Rate: {m.win_rate:.2%} ({m.correct_predictions}/{m.total_predictions})",
            f"ROI: {m.roi:.2%}",
            f"Yield: {m.yield_pct:.2f}%",
            f"Total PnL: {m.total_pnl:.2f}",
            f"Average Odds: {m.average_odds:.2f}",
            f"Average Confidence: {m.average_confidence:.2%}",
            "",
            "--- STATISTICAL METRICS ---",
            f"Accuracy: {m.accuracy:.2%}",
            f"Brier Score: {m.brier_score:.4f}",
            f"Log Loss: {m.log_loss:.4f}",
            f"Calibration Error: {m.calibration_error:.4f}",
            "",
        ]

        if summary.market_breakdown:
            lines.append("--- MARKET BREAKDOWN ---")
            for mb in summary.market_breakdown:
                lines.append(
                    f"  {mb.market}: {mb.correct}/{mb.total} "
                    f"({mb.win_rate:.2%}), ROI={mb.roi:.2%}"
                )
            lines.append("")

        if summary.prediction_statistics:
            lines.append("--- PREDICTION STATISTICS ---")
            for ps in summary.prediction_statistics:
                lines.append(
                    f"  {ps.market}: {ps.total_predictions} predictions, "
                    f"Brier={ps.brier_score:.4f}"
                )
            lines.append("")

        if summary.signal_statistics:
            lines.append("--- SIGNAL STATISTICS ---")
            for ss in summary.signal_statistics:
                lines.append(
                    f"  {ss.signal_type}: {ss.total_signals} signals, "
                    f"win_rate={ss.win_rate:.2%}"
                )
            lines.append("")

        if m.best_market:
            lines.append(f"Best Market: {m.best_market}")
        if m.worst_market:
            lines.append(f"Worst Market: {m.worst_market}")

        lines.append("=" * 60)
        return "\n".join(lines)
