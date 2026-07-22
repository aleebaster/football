"""Cards predictor."""

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


class CardsPredictor(BasePredictor):
    """Predicts yellow/red card outcomes."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.CARDS)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        home_cards = float(features.get("home_avg_cards", 1.8))
        away_cards = float(features.get("away_avg_cards", 2.0))
        total_cards = home_cards + away_cards

        over_prob = 0.5 + (total_cards - 3.5) * 0.1
        over_prob = max(0.15, min(0.85, over_prob))
        under_prob = 1.0 - over_prob

        outcomes = {"over_3.5": round(over_prob, 4), "under_3.5": round(under_prob, 4)}
        distribution = ProbabilityDistribution(
            market=PredictionMarket.CARDS,
            outcomes=outcomes,
        )

        risk = PredictionRiskAssessment(
            level=RiskLevel.HIGH,
            score=0.7,
            factors=["Cards data often limited"],
        )

        explanation = PredictionExplanation(
            summary=f"Expected cards: {total_cards:.1f} — {'Over' if over_prob > 0.5 else 'Under'} 3.5",
            key_factors=[
                f"Home avg cards: {home_cards:.1f}",
                f"Away avg cards: {away_cards:.1f}",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.CARDS,
            distribution=distribution,
            confidence=0.30,
            risk=risk,
            explanation=explanation,
        )
