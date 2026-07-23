"""Backtesting Orchestrator — coordinates the full backtest pipeline."""

import time

from app.backtesting.calibration import BacktestCalibration
from app.backtesting.evaluator import BacktestEvaluator
from app.backtesting.metrics import BacktestMetricsCalculator
from app.backtesting.models import (
    BacktestRequest,
    BacktestResult,
)
from app.backtesting.persistence import BacktestPersistence
from app.backtesting.reporting import BacktestReporter
from app.backtesting.runner import BacktestRunner
from app.backtesting.validator import BacktestValidator
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestOrchestrator:
    """Coordinates the full backtest pipeline.

    Pipeline:
        BacktestRequest
        → Validation
        → Dataset Loading
        → Running (per match: Prediction → Signal → Evaluation)
        → Metrics Calculation
        → Reporting
        → Persistence
        → BacktestResult
    """

    def __init__(
        self,
        runner: BacktestRunner,
        evaluator: BacktestEvaluator,
        metrics_calculator: BacktestMetricsCalculator,
        reporter: BacktestReporter,
        validator: BacktestValidator,
        persistence: BacktestPersistence,
        calibration: BacktestCalibration,
    ) -> None:
        self._runner = runner
        self._evaluator = evaluator
        self._metrics = metrics_calculator
        self._reporter = reporter
        self._validator = validator
        self._persistence = persistence
        self._calibration = calibration

    async def run(self, request: BacktestRequest) -> BacktestResult:
        """Run a full backtest pipeline.

        Args:
            request: Backtest request.

        Returns:
            Complete BacktestResult.
        """
        start = time.perf_counter()

        # Step 1: Validate
        self._validator.validate_request(request)

        # Step 2: Run backtest
        result = await self._runner.run(request)

        # Step 3: Calculate metrics
        if result.evaluations:
            result.metrics = await self._metrics.calculate(result.evaluations)

        # Step 4: Generate report
        await self._reporter.generate(result)

        # Step 5: Collect calibration data
        await self._calibration.collect(result)

        # Step 6: Persist
        result.id = await self._persistence.save(result)

        # Finalize
        from datetime import UTC, datetime

        elapsed = time.perf_counter() - start
        result.duration_seconds = round(elapsed, 3)
        result.completed_at = datetime.now(UTC)

        logger.info(
            f"Backtest pipeline complete: {len(result.evaluations)} evaluations "
            f"in {elapsed:.1f}s"
        )
        return result
