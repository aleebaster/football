"""Interfaces for Prediction Engine predictors."""

from abc import ABC, abstractmethod
from typing import Any

from app.prediction.models import (
    MarketPrediction,
    PredictionMarket,
    ProbabilityDistribution,
)


class BasePredictor(ABC):
    """Abstract base class for all market predictors."""

    def __init__(self, market: PredictionMarket) -> None:
        self._market = market

    @property
    def market(self) -> PredictionMarket:
        return self._market

    @abstractmethod
    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        """Generate prediction for this market.

        Args:
            features: Feature vector from AI Analysis Engine.
            odds_data: Optional odds from provider layer.

        Returns:
            Market prediction with distribution and explanation.
        """
        ...

    @staticmethod
    def _normalize(
        outcomes: dict[str, float],
        market: PredictionMarket = PredictionMarket.MATCH_WINNER,
    ) -> ProbabilityDistribution:
        """Normalize probabilities to sum to 1.0."""
        total = sum(outcomes.values())
        if total <= 0:
            n = len(outcomes) or 1
            normalized = dict.fromkeys(outcomes, 1.0 / n)
        else:
            normalized = {k: v / total for k, v in outcomes.items()}
        return ProbabilityDistribution(market=market, outcomes=normalized)
