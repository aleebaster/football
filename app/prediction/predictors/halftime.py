"""Halftime result predictor."""

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


class HalftimePredictor(BasePredictor):
    """Predicts halftime result."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.HALFTIME)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        inputs = MarketMapper.get_winner_inputs(features)

        home_adv = (
            inputs["home_form_points"]
            + inputs["standings_advantage"] * 8
            + inputs["venue_advantage"] * 4
        )

        home_ht = 0.40 + home_adv * 0.015
        draw_ht = 0.32 - abs(home_adv) * 0.005
        away_ht = 0.28 - home_adv * 0.015

        home_ht = max(0.1, min(0.7, home_ht))
        draw_ht = max(0.15, min(0.6, draw_ht))
        away_ht = max(0.1, min(0.7, away_ht))

        total = home_ht + draw_ht + away_ht
        outcomes = {
            "home": round(home_ht / total, 4),
            "draw": round(draw_ht / total, 4),
            "away": round(away_ht / total, 4),
        }

        distribution = ProbabilityDistribution(
            market=PredictionMarket.HALFTIME,
            outcomes=outcomes,
        )

        confidence = 0.45
        risk = PredictionRiskAssessment(level=RiskLevel.MEDIUM, score=0.55)

        explanation = PredictionExplanation(
            summary=f"HT: home {outcomes['home']:.1%}, draw {outcomes['draw']:.1%}, away {outcomes['away']:.1%}",
            key_factors=[
                f"Home form: {inputs['home_form_points']}/15",
                f"Venue advantage: {inputs['venue_advantage']:+.2f}",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.HALFTIME,
            distribution=distribution,
            confidence=round(confidence, 3),
            risk=risk,
            explanation=explanation,
        )
