"""Backtesting Evaluator — evaluates predictions against actual outcomes."""

import math

from app.backtesting.models import EvaluationResult
from app.logging import get_logger
from app.prediction.models import PredictionMarket

logger = get_logger(__name__)


class BacktestEvaluator:
    """Evaluates individual predictions against actual match outcomes."""

    def __init__(self, default_stake: float = 1.0) -> None:
        self._default_stake = default_stake

    async def evaluate(
        self,
        fixture_id: int,
        predicted_outcome: str,
        predicted_probability: float,
        actual_outcome: str,
        odds: float,
        confidence: float = 0.5,
        risk_score: float = 0.5,
        market: PredictionMarket = PredictionMarket.MATCH_WINNER,
        signal_id: str = "",
        model_version: str = "1.0.0",
    ) -> EvaluationResult:
        """Evaluate a single prediction against actual outcome.

        Args:
            fixture_id: Fixture ID.
            predicted_outcome: Model's predicted outcome.
            predicted_probability: Model's predicted probability.
            actual_outcome: Actual match outcome.
            odds: Market odds for the predicted outcome.
            confidence: Model confidence.
            risk_score: Risk assessment score.
            market: Market type string.
            signal_id: Signal ID if applicable.
            model_version: Model version string.

        Returns:
            EvaluationResult with all metrics.
        """
        is_correct = predicted_outcome == actual_outcome
        stake = self._default_stake

        # Calculate PnL
        if is_correct:
            pnl = stake * (odds - 1.0)
        else:
            pnl = -stake

        roi = pnl / stake if stake > 0 else 0.0

        # Edge = model probability - implied probability
        implied_prob = 1.0 / odds if odds > 0 else 0.0
        edge = predicted_probability - implied_prob

        # Expected value
        ev = predicted_probability * (odds - 1.0) - (1 - predicted_probability)

        logger.debug(
            f"Evaluated fixture {fixture_id}: correct={is_correct}, "
            f"pnl={pnl:.2f}, roi={roi:.4f}, edge={edge:.4f}"
        )

        return EvaluationResult(
            fixture_id=fixture_id,
            market=market,
            predicted_outcome=predicted_outcome,
            predicted_probability=predicted_probability,
            actual_outcome=actual_outcome,
            is_correct=is_correct,
            odds=odds,
            stake=stake,
            pnl=round(pnl, 4),
            roi=round(roi, 4),
            edge=round(edge, 4),
            expected_value=round(ev, 4),
            confidence=confidence,
            risk_score=risk_score,
            signal_id=signal_id,
            model_version=model_version,
        )

    def calculate_brier_score(self, probability: float, outcome: bool) -> float:
        """Calculate Brier score for a single prediction.

        Args:
            probability: Predicted probability.
            outcome: Whether the event occurred (True/False).

        Returns:
            Brier score (lower is better).
        """
        target = 1.0 if outcome else 0.0
        return (probability - target) ** 2

    def calculate_log_loss(
        self, probability: float, outcome: bool, epsilon: float = 1e-15
    ) -> float:
        """Calculate log loss for a single prediction.

        Args:
            probability: Predicted probability.
            outcome: Whether the event occurred (True/False).
            epsilon: Small value to avoid log(0).

        Returns:
            Log loss (lower is better).
        """
        prob = max(epsilon, min(1.0 - epsilon, probability))
        if outcome:
            return -math.log(prob)
        return -math.log(1.0 - prob)
