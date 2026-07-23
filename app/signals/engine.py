"""Signal Engine — main entry point for signal generation.

Works exclusively through the Prediction Engine:
    Provider Layer → AI Engine → Prediction Engine → Signal Engine → Telegram / Dashboard
"""

from app.cache.base import CacheManager
from app.logging import get_logger
from app.prediction.models import PredictionMarket, PredictionResult
from app.signals.cache import SignalCache
from app.signals.cooldown import CooldownManager
from app.signals.deduplication import DeduplicationManager
from app.signals.filtering import SignalFilter
from app.signals.history import SignalHistoryStore
from app.signals.metrics import MetricsCollector
from app.signals.models import Signal, UserPreferences
from app.signals.notifications import NotificationEngine
from app.signals.orchestrator import SignalOrchestrator
from app.signals.performance import PerformanceEngine
from app.signals.persistence import SignalPersistence
from app.signals.portfolio import PortfolioManager
from app.signals.preferences import PreferencesManager
from app.signals.ranking import SignalRanker
from app.signals.registry import SignalGeneratorRegistry
from app.signals.roi import ROIEngine
from app.signals.scoring import SignalScorer
from app.signals.validator import SignalValidator
from app.signals.watchlist import WatchlistManager

logger = get_logger(__name__)


class SignalEngine:
    """Main entry point for the Signal Engine.

    Usage:
        engine = SignalEngine(cache_manager)
        signals = await engine.process(prediction_result)
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        registry: SignalGeneratorRegistry | None = None,
        validator: SignalValidator | None = None,
        signal_filter: SignalFilter | None = None,
        deduplication: DeduplicationManager | None = None,
        cooldown: CooldownManager | None = None,
        scorer: SignalScorer | None = None,
        ranker: SignalRanker | None = None,
        notifications: NotificationEngine | None = None,
        history: SignalHistoryStore | None = None,
        persistence: SignalPersistence | None = None,
        metrics: MetricsCollector | None = None,
    ) -> None:
        # Initialize cache
        self._cache = SignalCache(cache_manager)

        # Use provided dependencies or create defaults
        self._registry = registry or SignalGeneratorRegistry()
        if not registry:
            self._register_generators()

        self._validator = validator or SignalValidator()
        self._filter = signal_filter or SignalFilter()
        self._dedup = deduplication or DeduplicationManager()
        self._cooldown = cooldown or CooldownManager()
        self._scorer = scorer or SignalScorer()
        self._ranker = ranker or SignalRanker()
        self._notifications = notifications or NotificationEngine()
        self._history = history or SignalHistoryStore()
        self._persistence = persistence or SignalPersistence()
        self._metrics = metrics or MetricsCollector()

        # Initialize user management
        self._preferences_manager = PreferencesManager()
        self._watchlist_manager = WatchlistManager()
        self._portfolio_manager = PortfolioManager()

        # Initialize analytics
        self._roi_engine = ROIEngine(self._history)
        self._performance_engine = PerformanceEngine(self._history)

        # Initialize orchestrator
        self._orchestrator = SignalOrchestrator(
            registry=self._registry,
            validator=self._validator,
            signal_filter=self._filter,
            deduplication=self._dedup,
            cooldown=self._cooldown,
            scorer=self._scorer,
            ranker=self._ranker,
            notifications=self._notifications,
            history=self._history,
            persistence=self._persistence,
            cache=self._cache,
            metrics=self._metrics,
        )

        logger.info(f"Signal Engine initialized with {len(self._registry)} generators")

    def _register_generators(self) -> None:
        """Register all built-in signal generators."""
        from app.signals.generators.btts import BTTSSignalGenerator
        from app.signals.generators.handicap import HandicapSignalGenerator
        from app.signals.generators.live import LiveSignalGenerator
        from app.signals.generators.over_under import OverUnderSignalGenerator
        from app.signals.generators.value import ValueSignalGenerator
        from app.signals.generators.winner import WinnerSignalGenerator

        self._registry.register(WinnerSignalGenerator(), PredictionMarket.MATCH_WINNER)
        self._registry.register(
            OverUnderSignalGenerator(), PredictionMarket.OVER_UNDER_25
        )
        self._registry.register(BTTSSignalGenerator(), PredictionMarket.BTTS)
        self._registry.register(
            HandicapSignalGenerator(), PredictionMarket.ASIAN_HANDICAP
        )
        # Value and Live generators work across markets
        self._registry.register(ValueSignalGenerator(), PredictionMarket.DOUBLE_CHANCE)
        self._registry.register(LiveSignalGenerator(), PredictionMarket.CORNERS)

    async def process(
        self,
        prediction: PredictionResult,
        preferences: UserPreferences | None = None,
    ) -> list[Signal]:
        """Process a prediction through the signal pipeline.

        Args:
            prediction: Prediction result from Prediction Engine.
            preferences: Optional user preferences for filtering.

        Returns:
            List of generated signals.
        """
        return await self._orchestrator.process(prediction, preferences)

    async def process_request(
        self,
        prediction: PredictionResult,
        user_id: int | None = None,
    ) -> list[Signal]:
        """Process with user context.

        Args:
            prediction: Prediction result.
            user_id: Optional user ID for personalized filtering.

        Returns:
            List of generated signals.
        """
        preferences = None
        if user_id is not None:
            preferences = self._preferences_manager.get(user_id)
        return await self.process(prediction, preferences)

    def evaluate_cancellation(
        self,
        signal: Signal,
        reason: str = "",
    ) -> object:
        """Evaluate whether to send a cancellation notification."""
        return self._notifications.evaluate_cancellation(signal, reason)

    # User management
    @property
    def preferences(self) -> PreferencesManager:
        return self._preferences_manager

    @property
    def watchlist(self) -> WatchlistManager:
        return self._watchlist_manager

    @property
    def portfolio(self) -> PortfolioManager:
        return self._portfolio_manager

    # Analytics
    @property
    def roi(self) -> ROIEngine:
        return self._roi_engine

    @property
    def performance(self) -> PerformanceEngine:
        return self._performance_engine

    # History & Persistence
    @property
    def history(self) -> SignalHistoryStore:
        return self._history

    @property
    def persistence(self) -> SignalPersistence:
        return self._persistence

    # Monitoring
    @property
    def metrics(self) -> MetricsCollector:
        return self._metrics

    @property
    def registry(self) -> SignalGeneratorRegistry:
        return self._registry

    def __len__(self) -> int:
        return len(self._registry)
