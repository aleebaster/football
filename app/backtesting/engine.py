"""Backtesting Engine — main entry point for the backtesting platform.

Reuses existing components without duplicating logic:
    Historical Matches → Provider Layer → AI Engine → Prediction Engine →
    Signal Engine → Backtesting Engine → Metrics → Reports → Calibration Dataset
"""

from app.backtesting.cache import BacktestCache
from app.backtesting.calibration import BacktestCalibration
from app.backtesting.evaluator import BacktestEvaluator
from app.backtesting.metrics import BacktestMetricsCalculator
from app.backtesting.models import BacktestRequest, BacktestResult, BacktestScope
from app.backtesting.orchestrator import BacktestOrchestrator
from app.backtesting.persistence import BacktestPersistence
from app.backtesting.reporting import BacktestReporter
from app.backtesting.statistics import BacktestStatistics
from app.backtesting.validator import BacktestValidator
from app.logging import get_logger
from app.prediction.engine import PredictionEngine
from app.signals.engine import SignalEngine

logger = get_logger(__name__)


class BacktestEngine:
    """Main entry point for the Backtesting Platform.

    All dependencies are injected through the constructor.
    The container builds the full dependency graph externally.

    Usage:
        engine = container.backtest_engine
        result = await engine.run(BacktestRequest(scope="single_match", fixture_id=123))
    """

    def __init__(
        self,
        prediction_engine: PredictionEngine,
        signal_engine: SignalEngine,
        orchestrator: BacktestOrchestrator,
        evaluator: BacktestEvaluator,
        metrics: BacktestMetricsCalculator,
        reporter: BacktestReporter,
        persistence: BacktestPersistence,
        calibration: BacktestCalibration,
        statistics: BacktestStatistics,
        cache: BacktestCache,
        validator: BacktestValidator | None = None,
    ) -> None:
        self._prediction_engine = prediction_engine
        self._signal_engine = signal_engine
        self._orchestrator = orchestrator
        self._evaluator = evaluator
        self._metrics = metrics
        self._reporter = reporter
        self._persistence = persistence
        self._calibration = calibration
        self._statistics = statistics
        self._cache = cache
        self._validator = validator or BacktestValidator()

        logger.info("Backtest Engine initialized via dependency injection")

    async def run(self, request: BacktestRequest) -> BacktestResult:
        """Run a backtest.

        Args:
            request: Backtest request with scope and parameters.

        Returns:
            Complete backtest result.
        """
        return await self._orchestrator.run(request)

    async def run_single(self, fixture_id: int) -> BacktestResult:
        """Run a backtest for a single match.

        Args:
            fixture_id: Fixture ID to backtest.

        Returns:
            Backtest result.
        """
        request = BacktestRequest(
            scope=BacktestScope.SINGLE_MATCH,
            fixture_id=fixture_id,
        )
        return await self.run(request)

    @property
    def statistics(self) -> BacktestStatistics:
        return self._statistics

    @property
    def calibration(self) -> BacktestCalibration:
        return self._calibration

    @property
    def persistence(self) -> BacktestPersistence:
        return self._persistence

    @property
    def metrics(self) -> BacktestMetricsCalculator:
        return self._metrics

    @property
    def reporter(self) -> BacktestReporter:
        return self._reporter

    @property
    def evaluator(self) -> BacktestEvaluator:
        return self._evaluator
