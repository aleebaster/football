"""Prediction Calibration — adjusts raw probabilities for accuracy.

Architecture is ready for future training on historical results
without changing the Prediction Engine.
"""

from app.logging import get_logger
from app.prediction.models import ProbabilityDistribution

logger = get_logger(__name__)


class CalibrationEngine:
    """Calibrates raw prediction probabilities.

    Current implementation uses simple isotonic-style calibration.
    Ready for future ML-based calibration via calibration_data.
    """

    def __init__(self) -> None:
        self._calibration_offsets: dict[str, dict[str, float]] = {}

    def calibrate(
        self,
        distribution: ProbabilityDistribution,
    ) -> ProbabilityDistribution:
        """Apply calibration adjustments to a probability distribution."""
        offsets = self._calibration_offsets.get(distribution.market.value, {})
        if not offsets:
            return distribution

        adjusted = dict(distribution.outcomes)
        for outcome, offset in offsets.items():
            if outcome in adjusted:
                adjusted[outcome] = max(0.01, adjusted[outcome] + offset)

        # Re-normalize
        total = sum(adjusted.values())
        if total <= 0:
            return distribution
        normalized = {k: v / total for k, v in adjusted.items()}
        return ProbabilityDistribution(
            market=distribution.market,
            outcomes=normalized,
        )

    def set_offsets(self, market: str, offsets: dict[str, float]) -> None:
        """Set calibration offsets for a market (for future training)."""
        self._calibration_offsets[market] = offsets
        logger.info(f"Calibration offsets set for {market}: {offsets}")

    def get_offsets(self, market: str) -> dict[str, float]:
        return self._calibration_offsets.get(market, {})
