"""Value Bet Engine — identifies value betting opportunities."""

from app.logging import get_logger
from app.prediction.models import (
    KellyResult,
    ProbabilityDistribution,
    ValueBet,
)

logger = get_logger(__name__)

KELLY_FRACTION = 0.25  # Quarter-Kelly for safety


class ValueBetEngine:
    """Compares model probabilities against market odds to find value."""

    def find_value(
        self,
        distribution: ProbabilityDistribution,
        odds: dict[str, float],
    ) -> list[ValueBet]:
        """Find value bets for a given distribution and odds."""
        value_bets: list[ValueBet] = []

        for outcome, model_prob in distribution.outcomes.items():
            market_odds = odds.get(outcome)
            if market_odds is None or market_odds <= 1.0:
                continue

            implied = 1.0 / market_odds
            edge = model_prob - implied
            ev = (model_prob * market_odds) - 1.0
            kelly = self._kelly(model_prob, market_odds)

            if edge > 0.02:  # Minimum 2% edge
                vb = ValueBet(
                    market=distribution.market,
                    outcome=outcome,
                    model_probability=round(model_prob, 4),
                    market_odds=round(market_odds, 2),
                    implied_probability=round(implied, 4),
                    edge=round(edge, 4),
                    expected_value=round(ev, 4),
                    kelly=kelly,
                    explanation=self._explain(outcome, model_prob, implied, edge),
                )
                value_bets.append(vb)
                logger.debug(f"Value bet found: {outcome} edge={edge:.2%} EV={ev:.2%}")

        value_bets.sort(key=lambda vb: vb.edge, reverse=True)
        return value_bets

    def _kelly(self, probability: float, odds: float) -> KellyResult:
        """Calculate Kelly criterion for a single bet."""
        b = odds - 1.0
        if b <= 0:
            return KellyResult()
        q = 1.0 - probability
        fraction = ((b * probability) - q) / b
        fraction = max(0.0, min(1.0, fraction * KELLY_FRACTION))
        edge = (probability * odds) - 1.0
        ev = (probability * odds) - 1.0
        return KellyResult(
            fraction=round(fraction, 4),
            edge=round(edge, 4),
            expected_value=round(ev, 4),
            recommended=fraction > 0.01 and edge > 0.02,
        )

    @staticmethod
    def _explain(
        outcome: str,
        model_prob: float,
        implied: float,
        edge: float,
    ) -> str:
        return (
            f"Model assigns {model_prob:.1%} to {outcome} "
            f"vs market implied {implied:.1%} — edge of {edge:.1%}"
        )
