"""Composition Root — central DI container.

All services are assembled here in a single place.
Every engine (AI, Prediction, Signal, Backtesting) shares the same instances.
All properties return their concrete types for full MyPy benefit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.config import settings
from app.logging import get_logger
from app.providers.cache import ProviderCache
from app.providers.manager import ProviderManager
from app.providers.registry import ProviderRegistry

if TYPE_CHECKING:
    from app.ai.engine import AIEngine
    from app.backtesting.calibration import BacktestCalibration
    from app.backtesting.engine import BacktestEngine
    from app.backtesting.evaluator import BacktestEvaluator
    from app.backtesting.metrics import BacktestMetricsCalculator
    from app.backtesting.orchestrator import BacktestOrchestrator
    from app.backtesting.persistence import BacktestPersistence
    from app.backtesting.reporting import BacktestReporter
    from app.backtesting.runner import BacktestRunner
    from app.prediction.engine import PredictionEngine
    from app.signals.engine import SignalEngine

logger = get_logger(__name__)


class Container:
    """Central DI container — single source of truth for all service instances.

    All properties return concrete types for type safety.
    Usage:
        container = get_container()
        ai = container.ai_engine
        prediction = container.prediction_engine
        signal = container.signal_engine
        backtest = container.backtest_engine
    """

    def __init__(self) -> None:
        self._cache_manager: CacheManager | None = None
        self._provider_registry: ProviderRegistry | None = None
        self._provider_cache: ProviderCache | None = None
        self._provider_manager: ProviderManager | None = None
        self._ai_engine: AIEngine | None = None
        self._prediction_engine: PredictionEngine | None = None
        self._signal_engine: SignalEngine | None = None
        self._backtest_engine: BacktestEngine | None = None

    # ── Cache ────────────────────────────────────────────────────────

    @property
    def cache_manager(self) -> CacheManager:
        if self._cache_manager is None:
            backend = MemoryCache(
                max_size=settings.cache.max_size,
                default_ttl=settings.cache.ttl,
            )
            self._cache_manager = CacheManager(backend)
        return self._cache_manager

    # ── Providers ────────────────────────────────────────────────────

    @property
    def provider_registry(self) -> ProviderRegistry:
        if self._provider_registry is None:
            self._provider_registry = ProviderRegistry()
        return self._provider_registry

    @property
    def provider_cache(self) -> ProviderCache:
        if self._provider_cache is None:
            self._provider_cache = ProviderCache(self.cache_manager)
        return self._provider_cache

    @property
    def provider_manager(self) -> ProviderManager:
        if self._provider_manager is None:
            self._provider_manager = ProviderManager(
                registry=self.provider_registry,
                cache=self.provider_cache,
            )
        return self._provider_manager

    # ── AI Engine ────────────────────────────────────────────────────

    @property
    def ai_engine(self) -> AIEngine:
        if self._ai_engine is None:
            from app.ai.engine import AIEngine

            self._ai_engine = AIEngine(
                provider_manager=self.provider_manager,
                cache_manager=self.cache_manager,
            )
        return self._ai_engine

    # ── Prediction Engine ────────────────────────────────────────────

    @property
    def prediction_engine(self) -> PredictionEngine:
        if self._prediction_engine is None:
            from app.prediction.engine import PredictionEngine

            self._prediction_engine = PredictionEngine(
                ai_engine=self.ai_engine,
                cache_manager=self.cache_manager,
            )
        return self._prediction_engine

    # ── Signal Engine ────────────────────────────────────────────────

    @property
    def signal_engine(self) -> SignalEngine:
        if self._signal_engine is None:
            from app.signals.cooldown import CooldownManager
            from app.signals.deduplication import DeduplicationManager
            from app.signals.engine import SignalEngine
            from app.signals.filtering import SignalFilter
            from app.signals.history import SignalHistoryStore
            from app.signals.metrics import MetricsCollector
            from app.signals.notifications import NotificationEngine
            from app.signals.persistence import SignalPersistence
            from app.signals.ranking import SignalRanker
            from app.signals.registry import SignalGeneratorRegistry
            from app.signals.scoring import SignalScorer
            from app.signals.validator import SignalValidator

            self._signal_engine = SignalEngine(
                cache_manager=self.cache_manager,
                registry=SignalGeneratorRegistry(),
                validator=SignalValidator(),
                signal_filter=SignalFilter(),
                deduplication=DeduplicationManager(),
                cooldown=CooldownManager(),
                scorer=SignalScorer(),
                ranker=SignalRanker(),
                notifications=NotificationEngine(),
                history=SignalHistoryStore(),
                persistence=SignalPersistence(),
                metrics=MetricsCollector(),
            )
        return self._signal_engine

    # ── Backtesting Engine ───────────────────────────────────────────

    @property
    def backtest_engine(self) -> BacktestEngine:
        if self._backtest_engine is None:
            from app.backtesting.calibration import BacktestCalibration
            from app.backtesting.engine import BacktestEngine
            from app.backtesting.evaluator import BacktestEvaluator
            from app.backtesting.metrics import BacktestMetricsCalculator
            from app.backtesting.persistence import BacktestPersistence
            from app.backtesting.reporting import BacktestReporter
            from app.backtesting.statistics import BacktestStatistics

            evaluator = BacktestEvaluator()
            metrics = BacktestMetricsCalculator()
            persistence = BacktestPersistence()
            calibration = BacktestCalibration()
            statistics = BacktestStatistics(metrics_calculator=metrics)
            reporter = BacktestReporter(metrics)
            runner = self._build_backtest_runner(evaluator)
            orchestrator = self._build_backtest_orchestrator(
                runner=runner,
                evaluator=evaluator,
                metrics_calculator=metrics,
                reporter=reporter,
                persistence=persistence,
                calibration=calibration,
            )

            from app.backtesting.cache import BacktestCache

            cache = BacktestCache(self.cache_manager)

            self._backtest_engine = BacktestEngine(
                orchestrator=orchestrator,
                evaluator=evaluator,
                metrics=metrics,
                reporter=reporter,
                persistence=persistence,
                calibration=calibration,
                statistics=statistics,
                cache=cache,
            )
        return self._backtest_engine

    def _build_backtest_runner(self, evaluator: BacktestEvaluator) -> BacktestRunner:
        """Build the backtest runner."""
        from app.backtesting.dataset import BacktestDataset
        from app.backtesting.runner import BacktestRunner

        return BacktestRunner(
            prediction_engine=self.prediction_engine,
            signal_engine=self.signal_engine,
            dataset=BacktestDataset(self.provider_manager),
            evaluator=evaluator,
        )

    def _build_backtest_orchestrator(
        self,
        runner: BacktestRunner,
        evaluator: BacktestEvaluator,
        metrics_calculator: BacktestMetricsCalculator,
        reporter: BacktestReporter,
        persistence: BacktestPersistence,
        calibration: BacktestCalibration,
    ) -> BacktestOrchestrator:
        """Build the backtest orchestrator."""
        from app.backtesting.orchestrator import BacktestOrchestrator
        from app.backtesting.validator import BacktestValidator

        return BacktestOrchestrator(
            runner=runner,
            evaluator=evaluator,
            metrics_calculator=metrics_calculator,
            reporter=reporter,
            validator=BacktestValidator(),
            persistence=persistence,
            calibration=calibration,
        )

    # ── Cleanup ──────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset all singletons (useful for testing)."""
        self._cache_manager = None
        self._provider_registry = None
        self._provider_cache = None
        self._provider_manager = None
        self._ai_engine = None
        self._prediction_engine = None
        self._signal_engine = None
        self._backtest_engine = None
        logger.info("Container reset")


# ── Module-level singleton ───────────────────────────────────────────

_container: Container | None = None


def get_container() -> Container:
    """Get the global container singleton."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """Reset the global container (for testing)."""
    global _container
    if _container is not None:
        _container.reset()
    _container = None
