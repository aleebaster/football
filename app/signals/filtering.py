"""Signal Filtering — filters signals based on quality criteria."""

from datetime import UTC, datetime

from app.logging import get_logger
from app.signals.models import Signal, SignalStatus, UserPreferences

logger = get_logger(__name__)

# Default thresholds
DEFAULT_MIN_CONFIDENCE = 0.3
DEFAULT_MAX_RISK_SCORE = 0.8
DEFAULT_MIN_DATA_AGE_SECONDS = 3600  # 1 hour


class SignalFilter:
    """Filters signals based on quality criteria."""

    def __init__(
        self,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        max_risk_score: float = DEFAULT_MAX_RISK_SCORE,
    ) -> None:
        self._min_confidence = min_confidence
        self._max_risk_score = max_risk_score

    def should_keep(self, signal: Signal) -> bool:
        """Determine if a signal should be kept.

        Args:
            signal: Signal to evaluate.

        Returns:
            True if signal should be kept, False otherwise.
        """
        # Check if signal is active
        if signal.status != SignalStatus.ACTIVE:
            logger.debug(f"Signal {signal.id} filtered: not active")
            return False

        # Check confidence threshold
        if signal.confidence < self._min_confidence:
            logger.debug(
                f"Signal {signal.id} filtered: confidence {signal.confidence} "
                f"< {self._min_confidence}"
            )
            return False

        # Check risk threshold
        if signal.risk_score > self._max_risk_score:
            logger.debug(
                f"Signal {signal.id} filtered: risk {signal.risk_score} "
                f"> {self._max_risk_score}"
            )
            return False

        # Check for explanation
        if not signal.summary and not signal.key_factors:
            logger.debug(f"Signal {signal.id} filtered: no explanation")
            return False

        # Check data freshness
        age_seconds = (datetime.now(UTC) - signal.created_at).total_seconds()
        if age_seconds > DEFAULT_MIN_DATA_AGE_SECONDS:
            logger.debug(
                f"Signal {signal.id} filtered: data too old ({age_seconds:.0f}s)"
            )
            return False

        return True

    def filter_signals(self, signals: list[Signal]) -> list[Signal]:
        """Filter a list of signals.

        Args:
            signals: List of signals to filter.

        Returns:
            Filtered list of signals.
        """
        kept = [s for s in signals if self.should_keep(s)]
        filtered_count = len(signals) - len(kept)
        if filtered_count > 0:
            logger.info(f"Filtered {filtered_count} signals, kept {len(kept)}")
        return kept

    def apply_user_preferences(
        self, signal: Signal, preferences: UserPreferences
    ) -> bool:
        """Apply user preferences to filter signals.

        Args:
            signal: Signal to check against preferences.
            preferences: User preferences.

        Returns:
            True if signal passes user preferences, False otherwise.
        """
        if not preferences.enabled:
            return False

        # Check confidence threshold
        if signal.confidence < preferences.min_confidence:
            return False

        # Check allowed markets
        if (
            preferences.allowed_markets
            and signal.market not in preferences.allowed_markets
        ):
            return False

        # Check quiet hours (simplified - would need timezone handling)
        now = datetime.now(UTC)
        current_hour = now.hour
        if preferences.notification_start_hour <= preferences.notification_end_hour:
            if not (
                preferences.notification_start_hour
                <= current_hour
                < preferences.notification_end_hour
            ):
                return False
        else:
            if (
                preferences.notification_end_hour
                <= current_hour
                < preferences.notification_start_hour
            ):
                return False

        return True
