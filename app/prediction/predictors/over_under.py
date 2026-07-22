"""Over/Under 2.5 goals predictor."""

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


class OverUnderPredictor(BasePredictor):
    """Predicts Over/Under 2.5 goals."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.OVER_UNDER_25)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        inputs = MarketMapper.get_over_under_inputs(features)

        total_goals = inputs["total_expected_goals"]
        if total_goals <= 0:
            avg_scored = (inputs["home_avg_scored"] + inputs["away_avg_scored"]) / 2
            avg_conceded = (
                inputs["home_avg_conceded"] + inputs["away_avg_conceded"]
            ) / 2
            total_goals = (
                avg_scored + avg_conceded if (avg_scored + avg_conceded) > 0 else 2.5
            )

        # Poisson-like: P(>=3) = 1 - P(0) - P(1) - P(2)
        import math

        lam = max(total_goals, 0.1)
        p0 = math.exp(-lam)
        p1 = lam * math.exp(-lam)
        p2 = (lam**2 / 2) * math.exp(-lam)
        over_prob = 1.0 - p0 - p1 - p2
        under_prob = p0 + p1 + p2

        outcomes = {
            "over": round(max(0.05, over_prob), 4),
            "under": round(max(0.05, under_prob), 4),
        }
        total = sum(outcomes.values())
        outcomes = {k: round(v / total, 4) for k, v in outcomes.items()}

        distribution = ProbabilityDistribution(
            market=PredictionMarket.OVER_UNDER_25,
            outcomes=outcomes,
        )

        confidence = 0.5 + abs(total_goals - 2.5) * 0.1
        confidence = min(1.0, max(0.2, confidence))
        risk = PredictionRiskAssessment(level=RiskLevel.MEDIUM, score=0.5)

        explanation = PredictionExplanation(
            summary=f"Expected total goals: {total_goals:.2f} — {'Over' if over_prob > 0.5 else 'Under'} 2.5 favored",
            key_factors=[
                f"Total expected goals: {total_goals:.2f}",
                f"Over 2.5 probability: {over_prob:.1%}",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.OVER_UNDER_25,
            distribution=distribution,
            confidence=round(confidence, 3),
            risk=risk,
            explanation=explanation,
        )
