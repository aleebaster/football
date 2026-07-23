"""BTTS Signal Generator — generates signals for Both Teams to Score market."""

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


class BTTSSignalGenerator(BaseSignalGenerator):
    """Generates signals for Both Teams to Score market."""

    async def generate(self, prediction: PredictionResult) -> list[Signal]:
        """Generate BTTS signals from prediction result."""
        signals: list[Signal] = []

        btts_pred = None
        for pred in prediction.predictions:
            if pred.market == PredictionMarket.BTTS:
                btts_pred = pred
                break

        if btts_pred is None:
            return signals

        outcome, probability = btts_pred.distribution.primary_outcome

        for vb in btts_pred.value_bets:
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
                confidence=btts_pred.confidence,
                odds=vb.market_odds,
                value_category=value_cat,
                edge=vb.edge,
            )
            signals.append(signal)

        if not signals and btts_pred.confidence >= 0.5:
            odds = 1.0 / probability if probability > 0 else 1.0
            signal = self._create_signal(
                prediction=prediction,
                outcome=outcome,
                probability=probability,
                confidence=btts_pred.confidence,
                odds=odds,
                value_category=ValueCategory.NEUTRAL,
                edge=0.0,
            )
            signals.append(signal)

        logger.debug(
            f"Generated {len(signals)} BTTS signals for fixture {prediction.fixture_id}"
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
        """Create a BTTS signal."""
        priority = (
            SignalPriority.HIGH
            if value_category == ValueCategory.STRONG_VALUE
            else SignalPriority.MEDIUM
        )
        outcome_label = "BTTS Yes" if outcome == "yes" else "BTTS No"
        summary = f"{outcome_label}: {probability:.1%} probability at {odds:.2f} odds"

        return Signal(
            id=f"sig_{uuid.uuid4().hex[:12]}",
            fixture_id=prediction.fixture_id,
            home_team_id=prediction.home_team_id,
            away_team_id=prediction.away_team_id,
            signal_type=SignalType.NEW,
            priority=priority,
            market=PredictionMarket.BTTS,
            prediction_id=f"pred_{prediction.fixture_id}",
            outcome=outcome,
            probability=round(probability, 4),
            confidence=round(confidence, 4),
            odds=round(odds, 2),
            value_category=value_category,
            risk_level=prediction.overall_risk.level,
            risk_score=prediction.overall_risk.score,
            summary=summary,
            key_factors=[
                f"Outcome: {outcome_label}",
                f"Probability: {probability:.1%}",
            ],
            model_version=prediction.model_version,
        )
