"""Over/Under Signal Generator — generates signals for Over/Under 2.5 market."""

import uuid

from app.logging import get_logger
from app.prediction.models import PredictionMarket, PredictionResult
from app.signals.interfaces import BaseSignalGenerator
from app.signals.models import (
    Signal,
    SignalPriority,
    SignalType,
    ValueCategory,
)

logger = get_logger(__name__)


class OverUnderSignalGenerator(BaseSignalGenerator):
    """Generates signals for Over/Under 2.5 Goals market."""

    async def generate(self, prediction: PredictionResult) -> list[Signal]:
        """Generate over/under signals from prediction result."""
        signals: list[Signal] = []

        ou_pred = None
        for pred in prediction.predictions:
            if pred.market == PredictionMarket.OVER_UNDER_25:
                ou_pred = pred
                break

        if ou_pred is None:
            return signals

        outcome, probability = ou_pred.distribution.primary_outcome

        # Check value bets
        for vb in ou_pred.value_bets:
            value_cat = (
                ValueCategory.STRONG_VALUE
                if vb.edge >= 0.08
                else ValueCategory.VALUE
                if vb.edge >= 0.03
                else ValueCategory.NEUTRAL
            )
            signal = self._create_signal(
                prediction=prediction,
                outcome=vb.outcome,
                probability=vb.model_probability,
                confidence=ou_pred.confidence,
                odds=vb.market_odds,
                value_category=value_cat,
                edge=vb.edge,
            )
            signals.append(signal)

        if not signals and ou_pred.confidence >= 0.5:
            odds = 1.0 / probability if probability > 0 else 1.0
            signal = self._create_signal(
                prediction=prediction,
                outcome=outcome,
                probability=probability,
                confidence=ou_pred.confidence,
                odds=odds,
                value_category=ValueCategory.NEUTRAL,
                edge=0.0,
            )
            signals.append(signal)

        logger.debug(
            f"Generated {len(signals)} over/under signals for fixture "
            f"{prediction.fixture_id}"
        )
        return signals

    def _create_signal(
        self,
        prediction: PredictionResult,
        outcome: str,
        probability: float,
        confidence: float,
        odds: float,
        value_category: ValueCategory,
        edge: float,
    ) -> Signal:
        """Create a signal."""
        priority = (
            SignalPriority.HIGH
            if value_category == ValueCategory.STRONG_VALUE
            else SignalPriority.MEDIUM
        )
        risk_level = prediction.overall_risk.level

        outcome_label = "Over 2.5" if outcome == "over" else "Under 2.5"
        summary = f"{outcome_label}: {probability:.1%} probability at {odds:.2f} odds"

        return Signal(
            id=f"sig_{uuid.uuid4().hex[:12]}",
            fixture_id=prediction.fixture_id,
            home_team_id=prediction.home_team_id,
            away_team_id=prediction.away_team_id,
            signal_type=SignalType.NEW,
            priority=priority,
            market=PredictionMarket.OVER_UNDER_25,
            prediction_id=f"pred_{prediction.fixture_id}",
            outcome=outcome,
            probability=round(probability, 4),
            confidence=round(confidence, 4),
            odds=round(odds, 2),
            value_category=value_category,
            risk_level=risk_level,
            risk_score=prediction.overall_risk.score,
            summary=summary,
            key_factors=[
                f"Outcome: {outcome_label}",
                f"Probability: {probability:.1%}",
                f"Odds: {odds:.2f}",
            ],
            model_version=prediction.model_version,
        )
