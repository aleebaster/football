"""Backtesting Runner — executes backtests across different scopes."""

from typing import Any

from app.backtesting.dataset import BacktestDataset
from app.backtesting.evaluator import BacktestEvaluator
from app.backtesting.exceptions import BacktestRunError
from app.backtesting.models import (
    BacktestRequest,
    BacktestResult,
    BacktestStatus,
    EvaluationResult,
)
from app.logging import get_logger
from app.prediction.engine import PredictionEngine
from app.prediction.models import PredictionRequest
from app.signals.engine import SignalEngine

logger = get_logger(__name__)


class BacktestRunner:
    """Runs backtests across different scopes.

    Supports single match, date range, league, season, and all matches.
    """

    def __init__(
        self,
        prediction_engine: PredictionEngine,
        signal_engine: SignalEngine,
        dataset: BacktestDataset,
        evaluator: BacktestEvaluator,
    ) -> None:
        self._prediction_engine = prediction_engine
        self._signal_engine = signal_engine
        self._dataset = dataset
        self._evaluator = evaluator

    async def run(self, request: BacktestRequest) -> BacktestResult:
        """Run a backtest based on the request scope.

        Args:
            request: Backtest request with scope and parameters.

        Returns:
            BacktestResult with all evaluations.
        """
        result = BacktestResult(
            request=request,
            status=BacktestStatus.RUNNING,
        )

        try:
            # Load dataset
            matches = await self._dataset.load(request)
            logger.info(f"Running backtest on {len(matches)} matches")

            evaluations: list[EvaluationResult] = []

            for match in matches:
                try:
                    eval_results = await self._evaluate_match(match)
                    evaluations.extend(eval_results)
                except Exception as e:
                    logger.warning(f"Failed to evaluate match {match.get('id')}: {e}")
                    continue

            result.evaluations = evaluations
            result.status = BacktestStatus.COMPLETED
            logger.info(
                f"Backtest completed: {len(evaluations)} evaluations "
                f"from {len(matches)} matches"
            )

        except Exception as e:
            result.status = BacktestStatus.FAILED
            result.error = str(e)
            raise BacktestRunError(f"Backtest failed: {e}") from e

        return result

    async def _evaluate_match(self, match: dict[str, Any]) -> list[EvaluationResult]:
        """Evaluate a single match through the full pipeline.

        Args:
            match: Historical match data.

        Returns:
            List of evaluation results for the match.
        """
        fixture_id = match.get("id", 0)
        home_team_id = match.get("home_team_id", 0)
        away_team_id = match.get("away_team_id", 0)
        home_goals = match.get("home_goals", 0)
        away_goals = match.get("away_goals", 0)

        # Determine actual outcome
        if home_goals > away_goals:
            actual_outcome = "home"
        elif home_goals < away_goals:
            actual_outcome = "away"
        else:
            actual_outcome = "draw"

        evaluations: list[EvaluationResult] = []

        # Run prediction pipeline
        try:
            prediction_request = PredictionRequest(
                fixture_id=fixture_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                force_refresh=True,
            )
            prediction = await self._prediction_engine.predict(prediction_request)

            # Run signal pipeline
            try:
                await self._signal_engine.process(prediction)
            except Exception as e:
                logger.debug(f"Signal generation skipped for {fixture_id}: {e}")

            # Evaluate each market prediction
            for market_pred in prediction.predictions:
                if not market_pred.value_bets:
                    # Use the primary outcome from distribution
                    primary = market_pred.distribution.primary_outcome
                    predicted_outcome = primary[0]
                    predicted_prob = primary[1]
                    odds = 2.0  # Default odds if no value bet
                else:
                    best_bet = market_pred.value_bets[0]
                    predicted_outcome = best_bet.outcome
                    predicted_prob = best_bet.model_probability
                    odds = best_bet.market_odds

                eval_result = await self._evaluator.evaluate(
                    fixture_id=fixture_id,
                    predicted_outcome=predicted_outcome,
                    predicted_probability=predicted_prob,
                    actual_outcome=actual_outcome,
                    odds=odds,
                    confidence=market_pred.confidence,
                    risk_score=market_pred.risk.score,
                    market=market_pred.market,
                    model_version=prediction.model_version,
                )
                evaluations.append(eval_result)

        except Exception as e:
            logger.warning(f"Prediction failed for fixture {fixture_id}: {e}")

        return evaluations
