"""Live Signal Generator — generates signals for live matches."""

import uuid

from app.logging import get_logger
from app.prediction.models import PredictionResult
from app.signals.interfaces import BaseSignalGenerator
from app.signals.models import (
    Signal,
    SignalPriority,
    SignalType,
    ValueCategory,
)

logger = get_logger(__name__)


class LiveSignalGenerator(BaseSignalGenerator):
    """Generates signals for live match scenarios."""

    async def generate(self, prediction: PredictionResult) -> list[Signal]:
        """Generate live signals from prediction result.

        Live signals are generated when confidence is high enough
        and the prediction has strong value characteristics.
        """
        signals: list[Signal] = []

        for pred in prediction.predictions:
            if pred.confidence < 0.6:
                continue

            outcome, probability = pred.distribution.primary_outcome

            # Only generate live signals for high-confidence predictions
            if probability < 0.55:
                continue

            # Find the best value bet if any
            best_edge = 0.0
            best_odds = 1.0 / probability if probability > 0 else 1.0
            for vb in pred.value_bets:
                if vb.edge > best_edge:
                    best_edge = vb.edge
                    best_odds = vb.market_odds

            value_cat = (
                ValueCategory.STRONG_VALUE
                if best_edge >= 0.05
                else ValueCategory.VALUE
                if best_edge > 0
                else ValueCategory.NEUTRAL
            )

            signal = Signal(
                id=f"sig_{uuid.uuid4().hex[:12]}",
                fixture_id=prediction.fixture_id,
                home_team_id=prediction.home_team_id,
                away_team_id=prediction.away_team_id,
                signal_type=SignalType.LIVE,
                priority=SignalPriority.HIGH
                if best_edge >= 0.05
                else SignalPriority.MEDIUM,
                market=pred.market,
                prediction_id=f"pred_{prediction.fixture_id}",
                outcome=outcome,
                probability=round(probability, 4),
                confidence=round(pred.confidence, 4),
                odds=round(best_odds, 2),
                value_category=value_cat,
                risk_level=prediction.overall_risk.level,
                risk_score=prediction.overall_risk.score,
                summary=f"LIVE: {outcome} at {probability:.1%} (confidence: {pred.confidence:.0%})",
                key_factors=[
                    f"Live signal for {pred.market.value}",
                    f"Confidence: {pred.confidence:.0%}",
                ],
                model_version=prediction.model_version,
            )
            signals.append(signal)

        logger.debug(
            f"Generated {len(signals)} live signals for fixture {prediction.fixture_id}"
        )
        return signals
