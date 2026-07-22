"""Asian Handicap predictor."""

from typing import Any

from app.prediction.interfaces import BasePredictor
from app.prediction.markets import MarketMapper
from app.prediction.models import (
    MarketPrediction,
    PredictionExplanation,
    PredictionMarket,
    PredictionRiskAssessment,
    ProbabilityDistribution,
    RiskLevel,
)


class AsianHandicapPredictor(BasePredictor):
    """Predicts Asian Handicap outcomes."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.ASIAN_HANDICAP)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        inputs = MarketMapper.get_winner_inputs(features)

        home_adv = (
            inputs["home_form_points"]
            + inputs["standings_advantage"] * 10
            + inputs["venue_advantage"] * 5
            + inputs["h2h_advantage"] * 3
        )

        # Determine handicap based on advantage
        if home_adv > 3:
            handicap = "-0.5"
            home_prob = 0.55 + home_adv * 0.01
        elif home_adv < -3:
            handicap = "+0.5"
            home_prob = 0.55 + abs(home_adv) * 0.01
        else:
            handicap = "0"
            home_prob = 0.50

        home_prob = max(0.15, min(0.85, home_prob))
        away_prob = 1.0 - home_prob

        outcomes = {"home": round(home_prob, 4), "away": round(away_prob, 4)}
        distribution = ProbabilityDistribution(
            market=PredictionMarket.ASIAN_HANDICAP,
            outcomes=outcomes,
        )

        confidence = 0.5 + abs(home_adv) * 0.02
        confidence = min(1.0, max(0.2, confidence))
        risk = PredictionRiskAssessment(level=RiskLevel.MEDIUM, score=0.5)

        explanation = PredictionExplanation(
            summary=f"Asian Handicap {handicap}: home {home_prob:.1%}, away {away_prob:.1%}",
            key_factors=[
                f"Handicap line: {handicap}",
                f"Home advantage: {home_adv:+.1f}",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.ASIAN_HANDICAP,
            distribution=distribution,
            confidence=round(confidence, 3),
            risk=risk,
            explanation=explanation,
        )
