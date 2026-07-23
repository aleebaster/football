"""Signal Orchestrator — coordinates the full signal pipeline.

Pipeline: PredictionResult → Validation → Filtering → Ranking → Scoring →
          Risk Filter → User Preferences → Notification Decision → Signal
"""

import time

from app.logging import get_logger
from app.prediction.models import PredictionResult
from app.signals.cache import SignalCache
from app.signals.cooldown import CooldownManager
from app.signals.deduplication import DeduplicationManager
from app.signals.filtering import SignalFilter
from app.signals.history import SignalHistoryStore
from app.signals.metrics import MetricsCollector
from app.signals.models import (
    Signal,
    SignalNotification,
    UserPreferences,
)
from app.signals.notifications import NotificationEngine
from app.signals.persistence import SignalPersistence
from app.signals.ranking import SignalRanker
from app.signals.registry import SignalGeneratorRegistry
from app.signals.scoring import SignalScorer
from app.signals.validator import SignalValidator

logger = get_logger(__name__)


class SignalOrchestrator:
    """Coordinates the full signal pipeline.

    Pipeline:
        PredictionResult
        → Validation
        → Signal Generation
        → Filtering
        → Deduplication
        → Cooldown Check
        → Scoring
        → Ranking
        → Notification Decision
        → Signal
    """

    def __init__(
        self,
        registry: SignalGeneratorRegistry,
        validator: SignalValidator,
        signal_filter: SignalFilter,
        deduplication: DeduplicationManager,
        cooldown: CooldownManager,
        scorer: SignalScorer,
        ranker: SignalRanker,
        notifications: NotificationEngine,
        history: SignalHistoryStore,
        persistence: SignalPersistence,
        cache: SignalCache | None = None,
        metrics: MetricsCollector | None = None,
    ) -> None:
        self._registry = registry
        self._validator = validator
        self._filter = signal_filter
        self._dedup = deduplication
        self._cooldown = cooldown
        self._scorer = scorer
        self._ranker = ranker
        self._notifications = notifications
        self._history = history
        self._persistence = persistence
        self._cache = cache
        self._metrics = metrics or MetricsCollector()

    async def process(
        self,
        prediction: PredictionResult,
        preferences: UserPreferences | None = None,
    ) -> list[Signal]:
        """Process a prediction through the full signal pipeline.

        Args:
            prediction: Prediction result from Prediction Engine.
            preferences: Optional user preferences for filtering.

        Returns:
            List of processed signals.
        """
        start = time.perf_counter()

        # Step 1: Validate prediction
        self._validator.validate_prediction(prediction)
        self._metrics.record_processed()

        # Step 2: Check cache
        if self._cache:
            cached = await self._cache.get(prediction.fixture_id)
            if cached:
                logger.debug(
                    f"Returning cached signals for fixture {prediction.fixture_id}"
                )
                return []

        # Step 3: Generate signals from all registered generators
        all_signals: list[Signal] = []
        for market, generator in self._registry.get_all().items():
            try:
                signals = await generator.generate(prediction)
                all_signals.extend(signals)
            except Exception as e:
                logger.warning(f"Generator {market.value} failed: {e}")

        if not all_signals:
            logger.debug(f"No signals generated for fixture {prediction.fixture_id}")
            return []

        # Step 4: Filter signals
        filtered = self._filter.filter_signals(all_signals)
        self._metrics.record_filtered(len(all_signals) - len(filtered))

        # Step 5: Deduplicate
        unique = self._dedup.filter_duplicates(filtered)
        self._metrics.record_duplicate(len(filtered) - len(unique))

        # Step 6: Check cooldown and deduplication state
        ready: list[Signal] = []
        for signal in unique:
            if self._cooldown.is_on_cooldown(signal):
                self._metrics.record_cooldown()
                continue
            if self._dedup.is_duplicate(signal):
                self._metrics.record_duplicate()
                continue
            ready.append(signal)

        # Step 7: Score signals
        for signal in ready:
            signal.score = self._scorer.calculate_score(signal, prediction)
            signal.value_category = self._scorer.categorize_value(signal)
            self._dedup.register(signal)

        # Step 8: Rank signals
        ranked = self._ranker.rank(ready)

        # Step 9: Apply user preferences
        if preferences:
            ranked = [
                s for s in ranked if self._filter.apply_user_preferences(s, preferences)
            ]

        # Step 10: Make notification decisions
        for signal in ranked:
            notification = self._notifications.should_notify(signal, preferences)
            if notification.should_notify:
                self._cooldown.mark_sent(signal)

            # Store in history and persistence
            await self._history.store(signal)
            await self._persistence.save(signal)

        elapsed = (time.perf_counter() - start) * 1000
        self._metrics.record_processing_time(elapsed)
        self._metrics.record_generated(len(ranked))

        # Step 11: Cache results
        if self._cache and ranked:
            await self._cache.set(
                prediction.fixture_id,
                [s.model_dump(mode="json") for s in ranked],
            )

        logger.info(
            f"Signal pipeline complete for fixture {prediction.fixture_id}: "
            f"{len(ranked)} signals generated in {elapsed:.1f}ms"
        )
        return ranked

    async def evaluate_update(
        self,
        old_signal: Signal,
        new_prediction: PredictionResult,
        preferences: UserPreferences | None = None,
    ) -> SignalNotification | None:
        """Evaluate whether to send an update notification.

        Args:
            old_signal: Previous signal.
            new_prediction: Updated prediction.
            preferences: Optional user preferences.

        Returns:
            Notification decision or None if no update needed.
        """
        # Generate new signals
        signals = await self.process(new_prediction, preferences)

        # Find matching signal
        for signal in signals:
            if (
                signal.fixture_id == old_signal.fixture_id
                and signal.market == old_signal.market
                and signal.outcome == old_signal.outcome
            ):
                return self._notifications.evaluate_update(old_signal, signal)

        return None
