"""BTTS (Both Teams To Score) predictor."""

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


class BTTSPredictor(BasePredictor):
    """Predicts whether both teams will score."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.BTTS)

    async def predict(
        self,
        features: dict[str, Any],
        odds_data: dict[str, float] | None = None,
    ) -> MarketPrediction:
        inputs = MarketMapper.get_btts_inputs(features)

        home_scored = inputs["home_avg_scored"]
        away_scored = inputs["away_avg_scored"]
        home_conceded = inputs["home_avg_conceded"]
        away_conceded = inputs["away_avg_conceded"]

        # BTTS Yes if both teams score AND concede on average
        home_scores_prob = min(1.0, home_scored / 1.5) if home_scored > 0 else 0.3
        away_scores_prob = min(1.0, away_scored / 1.5) if away_scored > 0 else 0.3
        home_concedes_prob = min(1.0, home_conceded / 1.2) if home_conceded > 0 else 0.3
        away_concedes_prob = min(1.0, away_conceded / 1.2) if away_conceded > 0 else 0.3

        btts_yes = (
            home_scores_prob
            * away_concedes_prob
            * away_scores_prob
            * home_concedes_prob
        )
        btts_no = 1.0 - btts_yes

        btts_yes = max(0.1, min(0.9, btts_yes))
        btts_no = 1.0 - btts_yes

        outcomes = {"yes": round(btts_yes, 4), "no": round(btts_no, 4)}

        distribution = ProbabilityDistribution(
            market=PredictionMarket.BTTS,
            outcomes=outcomes,
        )

        confidence = 0.5
        if home_scored > 0 and away_scored > 0:
            confidence = 0.6
        risk = PredictionRiskAssessment(level=RiskLevel.MEDIUM, score=0.5)

        explanation = PredictionExplanation(
            summary=f"BTTS {'Yes' if btts_yes > 0.5 else 'No'}: {btts_yes:.1%}",
            key_factors=[
                f"Home avg scored: {home_scored:.2f}, conceded: {home_conceded:.2f}",
                f"Away avg scored: {away_scored:.2f}, conceded: {away_conceded:.2f}",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.BTTS,
            distribution=distribution,
            confidence=round(confidence, 3),
            risk=risk,
            explanation=explanation,
        )
