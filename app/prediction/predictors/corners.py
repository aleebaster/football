"""Corners predictor."""

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


class CornersPredictor(BasePredictor):
    """Predicts corner kick outcomes."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.CORNERS)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        home_corners = float(features.get("home_avg_corners", 5.0))
        away_corners = float(features.get("away_avg_corners", 4.5))
        total_corners = home_corners + away_corners

        over_prob = 0.5 + (total_corners - 9.5) * 0.08
        over_prob = max(0.15, min(0.85, over_prob))
        under_prob = 1.0 - over_prob

        outcomes = {"over_9.5": round(over_prob, 4), "under_9.5": round(under_prob, 4)}
        distribution = ProbabilityDistribution(
            market=PredictionMarket.CORNERS,
            outcomes=outcomes,
        )

        risk = PredictionRiskAssessment(
            level=RiskLevel.HIGH,
            score=0.7,
            factors=["Corners data often limited"],
        )

        explanation = PredictionExplanation(
            summary=f"Expected corners: {total_corners:.1f} — {'Over' if over_prob > 0.5 else 'Under'} 9.5",
            key_factors=[
                f"Home avg corners: {home_corners:.1f}",
                f"Away avg corners: {away_corners:.1f}",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.CORNERS,
            distribution=distribution,
            confidence=0.35,
            risk=risk,
            explanation=explanation,
        )
