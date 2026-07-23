"""Composition Root — central DI container.

All services are assembled here in a single place.
Every engine (AI, Prediction, Signal, Backtesting) shares the same instances.
"""

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class Container:
    """Central DI container — single source of truth for all service instances.

    Usage:
        container = Container.create()
        ai_engine = container.ai_engine
        prediction_engine = container.prediction_engine
        signal_engine = container.signal_engine
        backtest_engine = container.backtest_engine
    """

    def __init__(self) -> None:
        # Lazy-initialized singletons
        self._cache_manager: CacheManager | None = None
        self._provider_registry: object | None = None
        self._provider_cache: object | None = None
        self._provider_manager: object | None = None
        self._ai_engine: object | None = None
        self._prediction_engine: object | None = None
        self._signal_engine: object | None = None
        self._backtest_engine: object | None = None

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
    def provider_registry(self) -> object:
        if self._provider_registry is None:
            from app.providers.registry import ProviderRegistry

            self._provider_registry = ProviderRegistry()
        return self._provider_registry

    @property
    def provider_cache(self) -> object:
        if self._provider_cache is None:
            from app.providers.cache import ProviderCache

            self._provider_cache = ProviderCache(self.cache_manager)
        return self._provider_cache

    @property
    def provider_manager(self) -> object:
        if self._provider_manager is None:
            from app.providers.manager import ProviderManager

            self._provider_manager = ProviderManager(
                registry=self.provider_registry,  # type: ignore[arg-type]
                cache=self.provider_cache,  # type: ignore[arg-type]
            )
        return self._provider_manager

    # ── AI Engine ────────────────────────────────────────────────────

    @property
    def ai_engine(self) -> object:
        if self._ai_engine is None:
            from app.ai.engine import AIEngine

            self._ai_engine = AIEngine(
                provider_manager=self.provider_manager,  # type: ignore[arg-type]
                cache_manager=self.cache_manager,
            )
        return self._ai_engine

    # ── Prediction Engine ────────────────────────────────────────────

    @property
    def prediction_engine(self) -> object:
        if self._prediction_engine is None:
            from app.prediction.engine import PredictionEngine

            self._prediction_engine = PredictionEngine(
                ai_engine=self.ai_engine,  # type: ignore[arg-type]
                cache_manager=self.cache_manager,
            )
        return self._prediction_engine

    # ── Signal Engine ────────────────────────────────────────────────

    @property
    def signal_engine(self) -> object:
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
    def backtest_engine(self) -> object:
        if self._backtest_engine is None:
            from app.backtesting.cache import BacktestCache
            from app.backtesting.calibration import BacktestCalibration
            from app.backtesting.dataset import BacktestDataset
            from app.backtesting.engine import BacktestEngine
            from app.backtesting.evaluator import BacktestEvaluator
            from app.backtesting.metrics import BacktestMetricsCalculator
            from app.backtesting.orchestrator import BacktestOrchestrator
            from app.backtesting.persistence import BacktestPersistence
            from app.backtesting.reporting import BacktestReporter
            from app.backtesting.runner import BacktestRunner
            from app.backtesting.statistics import BacktestStatistics
            from app.backtesting.validator import BacktestValidator

            # Shared components
            evaluator = BacktestEvaluator()
            metrics = BacktestMetricsCalculator()
            persistence = BacktestPersistence()
            calibration = BacktestCalibration()
            statistics = BacktestStatistics()
            dataset = BacktestDataset(self.provider_manager)  # type: ignore[arg-type]

            runner = BacktestRunner(
                prediction_engine=self.prediction_engine,  # type: ignore[arg-type]
                signal_engine=self.signal_engine,  # type: ignore[arg-type]
                dataset=dataset,
                evaluator=evaluator,
            )

            orchestrator = BacktestOrchestrator(
                runner=runner,
                evaluator=evaluator,
                metrics_calculator=metrics,
                reporter=BacktestReporter(metrics),
                validator=BacktestValidator(),
                persistence=persistence,
                calibration=calibration,
            )

            self._backtest_engine = BacktestEngine(
                prediction_engine=self.prediction_engine,  # type: ignore[arg-type]
                signal_engine=self.signal_engine,  # type: ignore[arg-type]
                orchestrator=orchestrator,
                evaluator=evaluator,
                metrics=metrics,
                reporter=BacktestReporter(metrics),
                persistence=persistence,
                calibration=calibration,
                statistics=statistics,
                cache=BacktestCache(self.cache_manager),
            )
        return self._backtest_engine

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
    """Get the global container singleton.

    Returns:
        The global Container instance.
    """
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
