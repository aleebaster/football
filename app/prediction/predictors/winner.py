"""Match Winner predictor — 1X2 market."""

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


class WinnerPredictor(BasePredictor):
    """Predicts match winner (Home / Draw / Away)."""

    def __init__(self) -> None:
        super().__init__(PredictionMarket.MATCH_WINNER)

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
            + inputs["home_momentum"] * 2
        )
        away_adv = (
            inputs["away_form_points"]
            + inputs["standings_advantage"] * -10
            + inputs["venue_advantage"] * -5
            + inputs["h2h_advantage"] * -3
            + inputs["away_momentum"] * 2
        )

        home_score = max(1.0, 50 + home_adv * 5)
        draw_score = max(1.0, 25 - abs(home_adv - away_adv) * 2)
        away_score = max(1.0, 50 + away_adv * 5)

        # Adjust with odds if available
        if odds_data and odds_data.get("home") and odds_data.get("away"):
            od_h = odds_data["home"]
            od_a = odds_data["away"]
            if od_h > 0 and od_a > 0:
                home_score = (home_score + (1 / od_h) * 100) / 2
                away_score = (away_score + (1 / od_a) * 100) / 2

        distribution = ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes={
                "home": home_score,
                "draw": draw_score,
                "away": away_score,
            },
        )
        # Normalize
        total = sum(distribution.outcomes.values())
        distribution = ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes={k: round(v / total, 4) for k, v in distribution.outcomes.items()},
        )

        # Confidence based on data availability
        confidence = min(
            1.0, len([v for v in inputs.values() if v != 0]) / max(len(inputs), 1)
        )

        risk = PredictionRiskAssessment(level=RiskLevel.MEDIUM, score=0.5)

        explanation = PredictionExplanation(
            summary=f"Home {'favored' if home_adv > away_adv else 'underdog'}: home form {inputs['home_form_points']}/15, away form {inputs['away_form_points']}/15",
            key_factors=[
                f"Form: home {inputs['home_form_points']}/15 vs away {inputs['away_form_points']}/15",
                f"Standings advantage: {inputs['standings_advantage']:+.2f}",
                f"Venue advantage: {inputs['venue_advantage']:+.2f}",
            ],
        )

        return MarketPrediction(
            market=PredictionMarket.MATCH_WINNER,
            distribution=distribution,
            confidence=round(confidence, 3),
            risk=risk,
            explanation=explanation,
        )
