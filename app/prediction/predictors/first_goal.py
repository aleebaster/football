"""First Goal scorer predictor."""

from typing import Any

from app.prediction.interfaces import BasePredictor
from app.prediction.models import (
    MarketPrediction,
    PredictionExplanation,
    PredictionMarket,
    PredictionRiskAssessment,
    ProbabilityDistribution,
    RiskLevel,
)


class FirstGoalPredictor(BasePredictor):
    """Predicts which team scores first."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.FIRST_GOAL)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        home_form = float(features.get("home_form_points", 7))
        away_form = float(features.get("away_form_points", 7))
        venue_adv = float(features.get("venue_advantage", 0))

        home_score = 0.40 + home_form * 0.01 + venue_adv * 0.1
        away_score = 0.40 + away_form * 0.01 - venue_adv * 0.1
        no_goal_score = 0.20

        total = home_score + away_score + no_goal_score
        outcomes = {
            "home": round(home_score / total, 4),
            "away": round(away_score / total, 4),
            "no_goal": round(no_goal_score / total, 4),
        }

        distribution = ProbabilityDistribution(
            market=PredictionMarket.FIRST_GOAL,
            outcomes=outcomes,
        )

        risk = PredictionRiskAssessment(level=RiskLevel.HIGH, score=0.65)

        explanation = PredictionExplanation(
            summary=f"First goal: home {outcomes['home']:.1%}, away {outcomes['away']:.1%}",
            key_factors=[
                f"Home form: {home_form}/15",
                f"Away form: {away_form}/15",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.FIRST_GOAL,
            distribution=distribution,
            confidence=0.35,
            risk=risk,
            explanation=explanation,
        )
