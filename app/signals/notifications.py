"""Notification Engine — decides when to send notifications.

Logic-only module — no Telegram API integration.
"""

from datetime import UTC, datetime, timedelta

from app.logging import get_logger
from app.signals.models import (
    Signal,
    SignalNotification,
    SignalPriority,
    SignalStatus,
    SignalType,
    UserPreferences,
)

logger = get_logger(__name__)


class NotificationEngine:
    """Decides when and how to notify users about signals."""

    def __init__(self) -> None:
        self._last_notifications: dict[str, datetime] = {}

    def should_notify(
        self,
        signal: Signal,
        preferences: UserPreferences | None = None,
    ) -> SignalNotification:
        """Decide whether to send a notification for this signal.

        Args:
            signal: Signal to evaluate.
            preferences: Optional user preferences.

        Returns:
            Notification decision.
        """
        # Default decision
        decision = SignalNotification(
            signal_id=signal.id,
            signal_type=signal.signal_type,
            priority=signal.priority,
            should_notify=False,
            notification_key=f"{signal.fixture_id}:{signal.market.value}",
        )

        # Don't notify for inactive signals
        if signal.status != SignalStatus.ACTIVE:
            decision.reason = "Signal is not active"
            return decision

        # Don't notify for negative EV
        from app.signals.models import ValueCategory

        if signal.value_category == ValueCategory.NEGATIVE_EV:
            decision.reason = "Negative expected value — not recommended"
            return decision

        # Check user preferences
        if preferences:
            if not preferences.enabled:
                decision.reason = "User notifications disabled"
                return decision

            if signal.confidence < preferences.min_confidence:
                decision.reason = (
                    f"Confidence {signal.confidence:.2f} below "
                    f"user threshold {preferences.min_confidence}"
                )
                return decision

            if (
                preferences.allowed_markets
                and signal.market not in preferences.allowed_markets
            ):
                decision.reason = f"Market {signal.market.value} not in allowed markets"
                return decision

            # Check quiet hours
            if not self._is_within_notification_hours(preferences):
                decision.reason = "Outside notification hours"
                return decision

        # Check cooldown between notifications
        notification_key = f"{signal.fixture_id}:{signal.market.value}"
        if notification_key in self._last_notifications:
            last_time = self._last_notifications[notification_key]
            min_interval = self._get_min_interval(signal.signal_type)
            if datetime.now(UTC) - last_time < min_interval:
                decision.reason = "Notification cooldown active"
                return decision

        # Signal passes all checks
        decision.should_notify = True
        decision.reason = "Signal meets all notification criteria"
        self._last_notifications[notification_key] = datetime.now(UTC)

        logger.debug(
            f"Notification approved for signal {signal.id} "
            f"(type={signal.signal_type.value}, priority={signal.priority.value})"
        )
        return decision

    def evaluate_update(
        self,
        old_signal: Signal,
        new_signal: Signal,
    ) -> SignalNotification:
        """Evaluate whether to send an update notification.

        Args:
            old_signal: Previous signal.
            new_signal: Updated signal.

        Returns:
            Notification decision.
        """
        decision = SignalNotification(
            signal_id=new_signal.id,
            signal_type=SignalType.UPDATE,
            priority=new_signal.priority,
            should_notify=False,
            notification_key=f"{new_signal.fixture_id}:{new_signal.market.value}",
        )

        # Check if confidence changed significantly
        conf_change = new_signal.confidence - old_signal.confidence
        if abs(conf_change) >= 0.1:
            if conf_change > 0:
                decision.signal_type = SignalType.CONFIDENCE_UP
                decision.priority = SignalPriority.HIGH
            else:
                decision.signal_type = SignalType.CONFIDENCE_DOWN
                decision.priority = SignalPriority.MEDIUM
            decision.should_notify = True
            decision.reason = f"Confidence changed by {conf_change:+.2f}"
            return decision

        # Check if outcome changed
        if old_signal.outcome != new_signal.outcome:
            decision.should_notify = True
            decision.signal_type = SignalType.UPDATE
            decision.reason = (
                f"Outcome changed from {old_signal.outcome} to {new_signal.outcome}"
            )
            return decision

        # Check if risk level changed
        if old_signal.risk_level != new_signal.risk_level:
            decision.should_notify = True
            decision.signal_type = SignalType.RISK_CHANGE
            decision.reason = f"Risk changed from {old_signal.risk_level.value} to {new_signal.risk_level.value}"
            return decision

        decision.reason = "No significant change detected"
        return decision

    def evaluate_cancellation(
        self,
        signal: Signal,
        reason: str = "",
    ) -> SignalNotification:
        """Evaluate whether to send a cancellation notification.

        Args:
            signal: Signal being cancelled.
            reason: Cancellation reason.

        Returns:
            Notification decision.
        """
        return SignalNotification(
            signal_id=signal.id,
            signal_type=SignalType.CANCEL,
            priority=SignalPriority.HIGH,
            should_notify=True,
            reason=reason or "Signal cancelled",
            notification_key=f"{signal.fixture_id}:{signal.market.value}",
        )

    def _is_within_notification_hours(self, preferences: UserPreferences) -> bool:
        """Check if current time is within user's notification hours."""
        now = datetime.now(UTC)
        current_hour = now.hour

        if preferences.notification_start_hour <= preferences.notification_end_hour:
            return (
                preferences.notification_start_hour
                <= current_hour
                < preferences.notification_end_hour
            )
        # Wraps around midnight
        return (
            current_hour >= preferences.notification_start_hour
            or current_hour < preferences.notification_end_hour
        )

    def _get_min_interval(self, signal_type: SignalType) -> timedelta:
        """Get minimum interval between notifications for a signal type."""
        intervals = {
            SignalType.NEW: timedelta(minutes=5),
            SignalType.UPDATE: timedelta(minutes=10),
            SignalType.LIVE: timedelta(minutes=5),
            SignalType.CONFIDENCE_UP: timedelta(hours=1),
            SignalType.CONFIDENCE_DOWN: timedelta(hours=1),
            SignalType.RISK_CHANGE: timedelta(hours=1),
        }
        return intervals.get(signal_type, timedelta(minutes=5))
