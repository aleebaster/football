"""Deduplication — prevents creation of duplicate signals."""

from app.logging import get_logger
from app.prediction.models import PredictionMarket
from app.signals.models import Signal, SignalType

logger = get_logger(__name__)


class DeduplicationManager:
    """Prevents creation of duplicate signals."""

    def __init__(self) -> None:
        self._seen: dict[str, str] = {}  # signal_key -> signal_id

    def _make_key(
        self,
        fixture_id: int,
        market: PredictionMarket,
        signal_type: SignalType = SignalType.NEW,
        prediction_version: str = "1.0.0",
    ) -> str:
        """Create a unique key for deduplication."""
        return f"{fixture_id}:{market.value}:{signal_type.value}:{prediction_version}"

    def _make_signal_key(self, signal: Signal) -> str:
        """Create a unique key from a signal."""
        return self._make_key(
            signal.fixture_id,
            signal.market,
            signal.signal_type,
            signal.model_version,
        )

    def is_duplicate(self, signal: Signal) -> bool:
        """Check if a signal is a duplicate.

        Args:
            signal: Signal to check.

        Returns:
            True if signal is a duplicate, False otherwise.
        """
        key = self._make_signal_key(signal)
        if key in self._seen:
            existing_id = self._seen[key]
            if existing_id != signal.id:
                logger.debug(f"Signal {signal.id} is duplicate of {existing_id}")
                return True
        return False

    def register(self, signal: Signal) -> None:
        """Register a signal as seen.

        Args:
            signal: Signal to register.
        """
        key = self._make_signal_key(signal)
        self._seen[key] = signal.id
        logger.debug(f"Registered signal {signal.id}")

    def invalidate(self, signal: Signal) -> None:
        """Invalidate a signal (e.g., on cancellation).

        Args:
            signal: Signal to invalidate.
        """
        key = self._make_signal_key(signal)
        self._seen.pop(key, None)
        logger.debug(f"Invalidated signal {signal.id}")

    def clear(self) -> None:
        """Clear all seen signals."""
        self._seen.clear()
        logger.info("Cleared all deduplication state")

    def filter_duplicates(self, signals: list[Signal]) -> list[Signal]:
        """Filter out duplicate signals.

        Args:
            signals: List of signals to deduplicate.

        Returns:
            List with duplicates removed.
        """
        seen_keys: set[str] = set()
        unique: list[Signal] = []
        duplicates = 0

        for signal in signals:
            key = self._make_signal_key(signal)
            if key not in seen_keys:
                seen_keys.add(key)
                unique.append(signal)
            else:
                duplicates += 1

        if duplicates > 0:
            logger.info(f"Removed {duplicates} duplicate signals")
        return unique
