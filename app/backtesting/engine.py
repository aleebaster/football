"""Backtesting Engine — main entry point for the backtesting platform.

Reuses existing components without duplicating logic:
    Historical Matches → Provider Layer → AI Engine → Prediction Engine →
    Signal Engine → Backtesting Engine → Metrics → Reports → Calibration Dataset
"""

from app.backtesting.cache import BacktestCache
from app.backtesting.calibration import BacktestCalibration
from app.backtesting.dataset import BacktestDataset
from app.backtesting.evaluator import BacktestEvaluator
from app.backtesting.metrics import BacktestMetricsCalculator
from app.backtesting.models import BacktestRequest, BacktestResult, BacktestScope
from app.backtesting.orchestrator import BacktestOrchestrator
from app.backtesting.persistence import BacktestPersistence
from app.backtesting.reporting import BacktestReporter
from app.backtesting.runner import BacktestRunner
from app.backtesting.statistics import BacktestStatistics
from app.backtesting.validator import BacktestValidator
from app.cache.base import CacheManager
from app.logging import get_logger
from app.prediction.engine import PredictionEngine
from app.providers.manager import ProviderManager
from app.signals.engine import SignalEngine

logger = get_logger(__name__)


class BacktestEngine:
    """Main entry point for the Backtesting Platform.

    Usage:
        engine = BacktestEngine(
            prediction_engine=prediction_engine,
            signal_engine=signal_engine,
            cache_manager=cache_manager,
            provider_manager=provider_manager,
        )
        result = await engine.run(BacktestRequest(scope="single_match", fixture_id=123))
    """

    def __init__(
        self,
        prediction_engine: PredictionEngine,
        signal_engine: SignalEngine,
        cache_manager: CacheManager | None = None,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        self._prediction_engine = prediction_engine
        self._signal_engine = signal_engine

        # Initialize components
        self._dataset = BacktestDataset(provider_manager)
        self._evaluator = BacktestEvaluator()
        self._metrics = BacktestMetricsCalculator()
        self._reporter = BacktestReporter(self._metrics)
        self._validator = BacktestValidator()
        self._persistence = BacktestPersistence()
        self._calibration = BacktestCalibration()
        self._cache = BacktestCache(cache_manager)
        self._statistics = BacktestStatistics()

        # Initialize runner
        self._runner = BacktestRunner(
            prediction_engine=prediction_engine,
            signal_engine=signal_engine,
            dataset=self._dataset,
            evaluator=self._evaluator,
        )

        # Initialize orchestrator
        self._orchestrator = BacktestOrchestrator(
            runner=self._runner,
            evaluator=self._evaluator,
            metrics_calculator=self._metrics,
            reporter=self._reporter,
            validator=self._validator,
            persistence=self._persistence,
            calibration=self._calibration,
        )

        logger.info("Backtest Engine initialized")

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
