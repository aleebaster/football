"""Winner Signal Generator — generates signals for Match Winner (1X2) market."""

import uuid

from app.logging import get_logger
from app.prediction.models import PredictionMarket, PredictionResult, ValueBet
from app.signals.interfaces import BaseSignalGenerator
from app.signals.models import (
    Signal,
    SignalPriority,
    SignalType,
    ValueCategory,
)

logger = get_logger(__name__)


class WinnerSignalGenerator(BaseSignalGenerator):
    """Generates signals for Match Winner (1X2) market."""

    async def generate(self, prediction: PredictionResult) -> list[Signal]:
        """Generate winner signals from prediction result."""
        signals: list[Signal] = []

        # Find winner market prediction
        winner_pred = None
        for pred in prediction.predictions:
            if pred.market == PredictionMarket.MATCH_WINNER:
                winner_pred = pred
                break

        if winner_pred is None:
            return signals

        # Get primary outcome
        outcome, probability = winner_pred.distribution.primary_outcome

        # Check for value bets
        value_bets = winner_pred.value_bets
        if value_bets:
            for vb in value_bets:
                signal = self._create_signal(
                    prediction=prediction,
                    outcome=vb.outcome,
                    probability=vb.model_probability,
                    confidence=winner_pred.confidence,
                    odds=vb.market_odds,
                    value_category=self._categorize_value(vb),
                    edge=vb.edge,
                )
                signals.append(signal)
        else:
            # Create signal for primary outcome if confidence is sufficient
            if winner_pred.confidence >= 0.5:
                # Estimate odds from probability
                odds = 1.0 / probability if probability > 0 else 1.0
                signal = self._create_signal(
                    prediction=prediction,
                    outcome=outcome,
                    probability=probability,
                    confidence=winner_pred.confidence,
                    odds=odds,
                    value_category=ValueCategory.NEUTRAL,
                    edge=0.0,
                )
                signals.append(signal)

        logger.debug(
            f"Generated {len(signals)} winner signals for fixture "
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
        """Create a signal for a winner outcome."""
        # Determine priority based on value category and confidence
        priority = self._determine_priority(value_category, confidence)

        # Determine risk level
        risk_level = prediction.overall_risk.level
        risk_score = prediction.overall_risk.score

        # Build explanation
        summary = self._build_summary(outcome, probability, confidence, odds, edge)
        key_factors = [
            f"Outcome: {outcome}",
            f"Probability: {probability:.1%}",
            f"Odds: {odds:.2f}",
        ]
        if edge > 0:
            key_factors.append(f"Edge: {edge:.1%}")
        if prediction.explanation:
            key_factors.extend(prediction.explanation.key_factors[:3])

        return Signal(
            id=f"sig_{uuid.uuid4().hex[:12]}",
            fixture_id=prediction.fixture_id,
            home_team_id=prediction.home_team_id,
            away_team_id=prediction.away_team_id,
            competition_id=None,
            signal_type=SignalType.NEW,
            priority=priority,
            market=PredictionMarket.MATCH_WINNER,
            prediction_id=f"pred_{prediction.fixture_id}",
            outcome=outcome,
            probability=round(probability, 4),
            confidence=round(confidence, 4),
            odds=round(odds, 2),
            value_category=value_category,
            risk_level=risk_level,
            risk_score=round(risk_score, 4),
            summary=summary,
            key_factors=key_factors,
            warnings=prediction.explanation.warnings if prediction.explanation else [],
            model_version=prediction.model_version,
        )

    def _categorize_value(self, vb: ValueBet) -> ValueCategory:
        """Categorize value bet."""
        if vb.edge >= 0.08:
            return ValueCategory.STRONG_VALUE
        if vb.edge >= 0.03:
            return ValueCategory.VALUE
        if vb.edge < 0:
            return ValueCategory.NEGATIVE_EV
        return ValueCategory.NEUTRAL

    def _determine_priority(
        self,
        value_category: ValueCategory,
        confidence: float,
    ) -> SignalPriority:
        """Determine signal priority."""
        if value_category == ValueCategory.STRONG_VALUE and confidence >= 0.7:
            return SignalPriority.CRITICAL
        if value_category == ValueCategory.STRONG_VALUE:
            return SignalPriority.HIGH
        if value_category == ValueCategory.VALUE and confidence >= 0.6:
            return SignalPriority.HIGH
        if value_category == ValueCategory.NEGATIVE_EV:
            return SignalPriority.LOW
        return SignalPriority.MEDIUM

    def _build_summary(
        self,
        outcome: str,
        probability: float,
        confidence: float,
        odds: float,
        edge: float,
    ) -> str:
        """Build human-readable summary."""
        outcome_label = {
            "home": "Home Win",
            "draw": "Draw",
            "away": "Away Win",
        }.get(outcome, outcome)

        if edge > 0.05:
            return (
                f"Strong value on {outcome_label}: "
                f"{probability:.1%} probability at {odds:.2f} odds "
                f"(edge: {edge:.1%})"
            )
        if edge > 0:
            return (
                f"Value on {outcome_label}: "
                f"{probability:.1%} probability at {odds:.2f} odds"
            )
        return (
            f"{outcome_label} predicted with "
            f"{probability:.1%} probability "
            f"(confidence: {confidence:.0%})"
        )
