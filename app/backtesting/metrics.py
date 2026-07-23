"""Backtesting Metrics — calculates aggregate metrics from evaluation results."""

import math
from collections import defaultdict

from app.backtesting.models import (
    BacktestMetrics,
    CalibrationBucket,
    EvaluationResult,
    MarketBreakdown,
    PredictionStatistics,
    SignalStatistics,
)
from app.logging import get_logger
from app.prediction.models import PredictionMarket

logger = get_logger(__name__)

CALIBRATION_BUCKETS = [
    (0.0, 0.1),
    (0.1, 0.2),
    (0.2, 0.3),
    (0.3, 0.4),
    (0.4, 0.5),
    (0.5, 0.6),
    (0.6, 0.7),
    (0.7, 0.8),
    (0.8, 0.9),
    (0.9, 1.0),
]


class BacktestMetricsCalculator:
    """Calculates aggregate metrics from evaluation results."""

    async def calculate(self, results: list[EvaluationResult]) -> BacktestMetrics:
        """Calculate comprehensive metrics from evaluation results."""
        if not results:
            return BacktestMetrics()

        total = len(results)
        correct = sum(1 for r in results if r.is_correct)
        incorrect = total - correct

        total_stake = sum(r.stake for r in results)
        total_pnl = sum(r.pnl for r in results)
        roi = total_pnl / total_stake if total_stake > 0 else 0.0
        yield_pct = roi * 100

        avg_odds = sum(r.odds for r in results) / total
        avg_confidence = sum(r.confidence for r in results) / total
        avg_risk = sum(r.risk_score for r in results) / total
        avg_edge = sum(r.edge for r in results) / total
        avg_ev = sum(r.expected_value for r in results) / total

        accuracy = correct / total if total > 0 else 0.0

        # Brier score and log loss
        brier_scores = []
        log_losses = []
        for r in results:
            prob = r.predicted_probability
            target = 1.0 if r.is_correct else 0.0
            brier_scores.append((prob - target) ** 2)
            eps = 1e-15
            clamped = max(eps, min(1.0 - eps, prob))
            log_losses.append(
                -math.log(clamped) if r.is_correct else -math.log(1.0 - clamped)
            )

        brier_score = sum(brier_scores) / len(brier_scores) if brier_scores else 0.0
        log_loss = sum(log_losses) / len(log_losses) if log_losses else 0.0
        calibration_error = self._calculate_calibration_error(results)

        # Find best/worst market
        market_stats = self.calculate_market_breakdown(results)
        best_market = None
        worst_market = None
        if market_stats:
            best = max(market_stats, key=lambda m: m.roi)
            worst = min(market_stats, key=lambda m: m.roi)
            best_market = best.market
            worst_market = worst.market

        return BacktestMetrics(
            total_predictions=total,
            correct_predictions=correct,
            incorrect_predictions=incorrect,
            win_rate=round(accuracy, 4),
            loss_rate=round(1.0 - accuracy, 4),
            roi=round(roi, 4),
            yield_pct=round(yield_pct, 2),
            total_stake=round(total_stake, 4),
            total_pnl=round(total_pnl, 4),
            average_odds=round(avg_odds, 4),
            average_confidence=round(avg_confidence, 4),
            average_risk=round(avg_risk, 4),
            average_edge=round(avg_edge, 4),
            average_ev=round(avg_ev, 4),
            accuracy=round(accuracy, 4),
            precision=round(accuracy, 4),
            recall=round(accuracy, 4),
            f1_score=round(accuracy, 4),
            brier_score=round(brier_score, 4),
            log_loss=round(log_loss, 4),
            calibration_error=round(calibration_error, 4),
            prediction_stability=round(1.0 - brier_score, 4),
            signal_accuracy=round(accuracy, 4),
            best_market=best_market,
            worst_market=worst_market,
        )

    def calculate_calibration_buckets(
        self, results: list[EvaluationResult]
    ) -> list[CalibrationBucket]:
        """Calculate calibration buckets."""
        bucket_data: dict[tuple[float, float], dict[str, int]] = {}
        for lower, upper in CALIBRATION_BUCKETS:
            bucket_data[(lower, upper)] = {"count": 0, "correct": 0}

        for r in results:
            for lower, upper in CALIBRATION_BUCKETS:
                if lower <= r.predicted_probability < upper:
                    bucket_data[(lower, upper)]["count"] += 1
                    if r.is_correct:
                        bucket_data[(lower, upper)]["correct"] += 1
                    break

        buckets = []
        for (lower, upper), data in bucket_data.items():
            count = data["count"]
            correct = data["correct"]
            observed = correct / count if count > 0 else 0.0
            expected = (lower + upper) / 2.0
            gap = abs(observed - expected)

            buckets.append(
                CalibrationBucket(
                    lower=lower,
                    upper=upper,
                    count=count,
                    correct=correct,
                    observed_frequency=round(observed, 4),
                    expected_frequency=round(expected, 4),
                    gap=round(gap, 4),
                )
            )
        return buckets

    def calculate_market_breakdown(
        self, results: list[EvaluationResult]
    ) -> list[MarketBreakdown]:
        """Calculate metrics broken down by market."""
        by_market: dict[PredictionMarket, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            by_market[r.market].append(r)

        breakdowns = []
        for market_key, market_results in by_market.items():
            total = len(market_results)
            correct = sum(1 for r in market_results if r.is_correct)
            win_rate = correct / total if total > 0 else 0.0
            total_stake = sum(r.stake for r in market_results)
            total_pnl = sum(r.pnl for r in market_results)
            roi = total_pnl / total_stake if total_stake > 0 else 0.0
            avg_odds = sum(r.odds for r in market_results) / total
            avg_conf = sum(r.confidence for r in market_results) / total

            breakdowns.append(
                MarketBreakdown(
                    market=market_key,
                    total=total,
                    correct=correct,
                    win_rate=round(win_rate, 4),
                    roi=round(roi, 4),
                    average_odds=round(avg_odds, 4),
                    average_confidence=round(avg_conf, 4),
                )
            )
        return breakdowns

    def calculate_prediction_statistics(
        self, results: list[EvaluationResult]
    ) -> list[PredictionStatistics]:
        """Calculate statistics per prediction market type."""
        by_market: dict[PredictionMarket, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            by_market[r.market].append(r)

        stats = []
        for market, market_results in by_market.items():
            total = len(market_results)
            correct = sum(1 for r in market_results if r.is_correct)
            total_pnl = sum(r.pnl for r in market_results)
            total_stake = sum(r.stake for r in market_results)
            avg_conf = sum(r.confidence for r in market_results) / total
            avg_odds = sum(r.odds for r in market_results) / total

            # Brier score for this market
            brier = 0.0
            for r in market_results:
                target = 1.0 if r.is_correct else 0.0
                brier += (r.predicted_probability - target) ** 2
            brier /= total if total > 0 else 1.0

            stats.append(
                PredictionStatistics(
                    market=market,
                    total_predictions=total,
                    correct_predictions=correct,
                    win_rate=round(correct / total if total > 0 else 0.0, 4),
                    roi=round(total_pnl / total_stake if total_stake > 0 else 0.0, 4),
                    average_confidence=round(avg_conf, 4),
                    average_odds=round(avg_odds, 4),
                    brier_score=round(brier, 4),
                )
            )
        return stats

    def calculate_signal_statistics(
        self, results: list[EvaluationResult]
    ) -> list[SignalStatistics]:
        """Calculate statistics per signal type (by signal_id presence)."""
        with_signal = [r for r in results if r.signal_id]
        without_signal = [r for r in results if not r.signal_id]

        stats = []
        for label, group in [
            ("with_signal", with_signal),
            ("without_signal", without_signal),
        ]:
            total = len(group)
            if total == 0:
                continue
            correct = sum(1 for r in group if r.is_correct)
            total_pnl = sum(r.pnl for r in group)
            total_stake = sum(r.stake for r in group)
            avg_conf = sum(r.confidence for r in group) / total

            stats.append(
                SignalStatistics(
                    signal_type=label,
                    total_signals=total,
                    winning_signals=correct,
                    win_rate=round(correct / total, 4),
                    roi=round(total_pnl / total_stake if total_stake > 0 else 0.0, 4),
                    average_confidence=round(avg_conf, 4),
                )
            )
        return stats

    def _calculate_calibration_error(self, results: list[EvaluationResult]) -> float:
        """Calculate Expected Calibration Error (ECE)."""
        buckets = self.calculate_calibration_buckets(results)
        total = sum(b.count for b in buckets)
        if total == 0:
            return 0.0

        ece = 0.0
        for bucket in buckets:
            if bucket.count > 0:
                weight = bucket.count / total
                ece += weight * bucket.gap
        return ece
