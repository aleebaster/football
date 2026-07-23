"""Signal Ranking — sorts signals by multiple quality metrics."""

from app.logging import get_logger
from app.signals.models import Signal, SignalRank

logger = get_logger(__name__)

# Multi-factor ranking weights
RANKING_WEIGHTS = {
    "overall": 0.25,
    "confidence": 0.15,
    "expected_value": 0.20,
    "risk": 0.10,  # Lower risk is better, will be inverted
    "historical_accuracy": 0.10,
    "prediction_stability": 0.08,
    "provider_quality": 0.07,
    "freshness": 0.05,
}


class SignalRanker:
    """Ranks signals by multiple quality criteria."""

    def _calculate_rank_score(self, signal: Signal) -> float:
        """Calculate composite ranking score for a signal.

        Higher score = better rank.

        Args:
            signal: Signal to score.

        Returns:
            Composite ranking score.
        """
        if not signal.score:
            return 0.0

        # Invert risk (lower risk = higher score)
        risk_inverted = 1.0 - signal.risk_score

        composite = (
            signal.score.overall * RANKING_WEIGHTS["overall"]
            + signal.score.confidence * RANKING_WEIGHTS["confidence"]
            + self._normalize_ev(signal.score.expected_value)
            * RANKING_WEIGHTS["expected_value"]
            + risk_inverted * RANKING_WEIGHTS["risk"]
            + signal.score.historical_accuracy * RANKING_WEIGHTS["historical_accuracy"]
            + signal.score.prediction_stability
            * RANKING_WEIGHTS["prediction_stability"]
            + signal.score.provider_quality * RANKING_WEIGHTS["provider_quality"]
            + signal.score.signal_freshness * RANKING_WEIGHTS["freshness"]
        )
        return composite

    def _normalize_ev(self, ev: float) -> float:
        """Normalize expected value to 0-1 range.

        Args:
            ev: Expected value.

        Returns:
            Normalized value between 0 and 1.
        """
        # Map EV range [-0.1, 0.2] to [0, 1]
        return max(0.0, min(1.0, (ev + 0.1) / 0.3))

    def rank(self, signals: list[Signal]) -> list[Signal]:
        """Rank signals by composite quality score.

        Args:
            signals: List of signals to rank.

        Returns:
            Ranked list with position and percentile set.
        """
        if not signals:
            return []

        # Calculate composite score for each signal
        scored = [(signal, self._calculate_rank_score(signal)) for signal in signals]

        # Sort by composite score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        sorted_signals = [s for s, _ in scored]

        # Assign ranks
        for idx, (signal, score) in enumerate(scored):
            percentile = 1.0 - (idx / len(scored))
            signal.rank = SignalRank(
                position=idx + 1,
                percentile=round(percentile, 3),
                comparison_score=round(score, 3),
            )

        logger.debug(f"Ranked {len(signals)} signals by multi-factor score")
        return sorted_signals
