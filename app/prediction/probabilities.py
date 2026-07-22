"""Probability Engine — computes and normalizes probability distributions."""

from app.logging import get_logger
from app.prediction.models import PredictionMarket, ProbabilityDistribution

logger = get_logger(__name__)

MIN_PROBABILITY = 0.01
MAX_PROBABILITY = 0.95


class ProbabilityEngine:
    """Computes and normalizes probability distributions."""

    def compute_match_winner(
        self,
        home_score: float,
        draw_score: float,
        away_score: float,
    ) -> ProbabilityDistribution:
        """Compute 1X2 probabilities from raw scores."""
        raw = {
            "home": max(home_score, MIN_PROBABILITY),
            "draw": max(draw_score, MIN_PROBABILITY),
            "away": max(away_score, MIN_PROBABILITY),
        }
        total = sum(raw.values())
        outcomes = {k: v / total for k, v in raw.items()}
        return ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes=outcomes,
        )

    def compute_btts(
        self,
        btts_yes_score: float,
        btts_no_score: float,
    ) -> ProbabilityDistribution:
        """Compute Both Teams To Score probabilities."""
        raw = {
            "yes": max(btts_yes_score, MIN_PROBABILITY),
            "no": max(btts_no_score, MIN_PROBABILITY),
        }
        total = sum(raw.values())
        return ProbabilityDistribution(
            market=PredictionMarket.BTTS,
            outcomes={k: v / total for k, v in raw.items()},
        )

    def compute_over_under(
        self,
        over_score: float,
        under_score: float,
    ) -> ProbabilityDistribution:
        """Compute Over/Under 2.5 probabilities."""
        raw = {
            "over": max(over_score, MIN_PROBABILITY),
            "under": max(under_score, MIN_PROBABILITY),
        }
        total = sum(raw.values())
        return ProbabilityDistribution(
            market=PredictionMarket.OVER_UNDER_25,
            outcomes={k: v / total for k, v in raw.items()},
        )

    def compute_double_chance(
        self,
        home_draw_score: float,
        home_away_score: float,
        draw_away_score: float,
    ) -> ProbabilityDistribution:
        """Compute Double Chance probabilities."""
        raw = {
            "1X": max(home_draw_score, MIN_PROBABILITY),
            "X2": max(draw_away_score, MIN_PROBABILITY),
            "12": max(home_away_score, MIN_PROBABILITY),
        }
        total = sum(raw.values())
        return ProbabilityDistribution(
            market=PredictionMarket.DOUBLE_CHANCE,
            outcomes={k: v / total for k, v in raw.items()},
        )

    def normalize(
        self,
        outcomes: dict[str, float],
        market: PredictionMarket = PredictionMarket.MATCH_WINNER,
    ) -> ProbabilityDistribution:
        """Normalize any set of outcomes to sum to 1.0."""
        total = sum(outcomes.values())
        if total <= 0:
            n = len(outcomes) or 1
            return ProbabilityDistribution(
                market=market,
                outcomes=dict.fromkeys(outcomes, 1.0 / n),
            )
        return ProbabilityDistribution(
            market=market,
            outcomes={k: max(v / total, MIN_PROBABILITY) for k, v in outcomes.items()},
        )

    @staticmethod
    def clip_probabilities(
        outcomes: dict[str, float],
        market: PredictionMarket = PredictionMarket.MATCH_WINNER,
    ) -> ProbabilityDistribution:
        """Clip probabilities to [MIN_PROBABILITY, MAX_PROBABILITY] and re-normalize."""
        clipped = {
            k: max(MIN_PROBABILITY, min(MAX_PROBABILITY, v))
            for k, v in outcomes.items()
        }
        total = sum(clipped.values())
        normalized = {k: v / total for k, v in clipped.items()}
        return ProbabilityDistribution(market=market, outcomes=normalized)
