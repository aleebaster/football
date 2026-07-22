"""Double Chance predictor — 1X, X2, 12 markets."""

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


class DoubleChancePredictor(BasePredictor):
    """Predicts double chance outcomes."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.DOUBLE_CHANCE)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        inputs = MarketMapper.get_double_chance_inputs(features)

        # Build base 1X2 from features
        home_adv = (
            inputs["home_form_points"]
            + inputs["standings_advantage"] * 10
            + inputs["venue_advantage"] * 5
            + inputs["h2h_advantage"] * 3
        )
        away_adv = inputs["away_form_points"] - home_adv

        home_prob = 0.40 + home_adv * 0.02
        draw_prob = 0.28
        away_prob = 0.32 + away_adv * 0.02

        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        outcomes = {
            "1X": round(home_prob + draw_prob, 4),
            "X2": round(draw_prob + away_prob, 4),
            "12": round(home_prob + away_prob, 4),
        }
        dc_total = sum(outcomes.values())
        outcomes = {k: round(v / dc_total, 4) for k, v in outcomes.items()}

        distribution = ProbabilityDistribution(
            market=PredictionMarket.DOUBLE_CHANCE,
            outcomes=outcomes,
        )

        confidence = min(
            1.0, len([v for v in inputs.values() if v != 0]) / max(len(inputs), 1)
        )
        risk = PredictionRiskAssessment(level=RiskLevel.LOW, score=0.3)

        explanation = PredictionExplanation(
            summary=f"Double chance: 1X={outcomes['1X']:.1%}, X2={outcomes['X2']:.1%}, 12={outcomes['12']:.1%}",
            key_factors=["Double chance covers two of three outcomes"],
        )

        return MarketPrediction(
            market=PredictionMarket.DOUBLE_CHANCE,
            distribution=distribution,
            confidence=round(confidence, 3),
            risk=risk,
            explanation=explanation,
        )
