"""Cooldown — prevents spam and repeated notifications."""

import time

from app.logging import get_logger
from app.signals.models import Signal, SignalType

logger = get_logger(__name__)

# Default cooldown periods in seconds
DEFAULT_COOLDOWNS = {
    SignalType.NEW: 300,  # 5 minutes
    SignalType.UPDATE: 600,  # 10 minutes
    SignalType.CANCEL: 0,  # No cooldown for cancellations
    SignalType.CONFIDENCE_UP: 3600,  # 1 hour
    SignalType.CONFIDENCE_DOWN: 3600,  # 1 hour
    SignalType.RISK_CHANGE: 3600,  # 1 hour
    SignalType.MATCH_START: 0,  # No cooldown
    SignalType.LIVE: 300,  # 5 minutes
    SignalType.MATCH_END: 0,  # No cooldown
}


class CooldownManager:
    """Manages signal cooldowns to prevent spam."""

    def __init__(self, cooldowns: dict[SignalType, int] | None = None) -> None:
        self._cooldowns = cooldowns or DEFAULT_COOLDOWNS
        self._last_sent: dict[str, float] = {}  # key -> timestamp

    def _make_key(self, signal: Signal) -> str:
        """Create a unique key for cooldown tracking."""
        return f"{signal.fixture_id}:{signal.market.value}:{signal.signal_type.value}"

    def is_on_cooldown(self, signal: Signal) -> bool:
        """Check if a signal is on cooldown.

        Args:
            signal: Signal to check.

        Returns:
            True if signal is on cooldown, False otherwise.
        """
        key = self._make_key(signal)
        if key not in self._last_sent:
            return False

        last_sent = self._last_sent[key]
        cooldown = self._cooldowns.get(signal.signal_type, 300)
        elapsed = time.time() - last_sent

        if elapsed < cooldown:
            logger.debug(
                f"Signal {signal.id} on cooldown: {cooldown - elapsed:.0f}s remaining"
            )
            return True
        return False

    def mark_sent(self, signal: Signal) -> None:
        """Mark a signal as sent.

        Args:
            signal: Signal that was sent.
        """
        key = self._make_key(signal)
        self._last_sent[key] = time.time()
        logger.debug(f"Marked signal {signal.id} as sent")

    def clear_cooldown(self, signal: Signal) -> None:
        """Clear cooldown for a signal.

        Args:
            signal: Signal to clear cooldown for.
        """
        key = self._make_key(signal)
        self._last_sent.pop(key, None)
        logger.debug(f"Cleared cooldown for signal {signal.id}")

    def clear_all(self) -> None:
        """Clear all cooldowns."""
        self._last_sent.clear()
        logger.info("Cleared all cooldowns")

    def get_remaining(self, signal: Signal) -> float:
        """Get remaining cooldown time in seconds.

        Args:
            signal: Signal to check.

        Returns:
            Remaining seconds, 0 if not on cooldown.
        """
        key = self._make_key(signal)
        if key not in self._last_sent:
            return 0.0

        last_sent = self._last_sent[key]
        cooldown = self._cooldowns.get(signal.signal_type, 300)
        elapsed = time.time() - last_sent
        remaining = max(0.0, cooldown - elapsed)
        return remaining
