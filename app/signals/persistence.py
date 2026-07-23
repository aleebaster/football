"""Persistence — prepares architecture for signal storage.

Currently uses in-memory storage.
Ready for PostgreSQL migration without changing business logic.
"""

from app.logging import get_logger
from app.signals.models import Signal, SignalHistory, SignalStatus

logger = get_logger(__name__)


class SignalPersistence:
    """In-memory persistence for signals.

    Ready for database persistence when needed.
    Business logic is isolated from storage implementation.
    """

    def __init__(self) -> None:
        self._active_signals: dict[str, Signal] = {}
        self._history: dict[str, list[SignalHistory]] = {}
        self._next_history_id = 1

    async def save(self, signal: Signal) -> None:
        """Save a signal."""
        self._active_signals[signal.id] = signal
        logger.debug(f"Saved signal {signal.id}")

    async def get(self, signal_id: str) -> Signal | None:
        """Get a signal by ID."""
        return self._active_signals.get(signal_id)

    async def get_by_fixture(self, fixture_id: int) -> list[Signal]:
        """Get all active signals for a fixture."""
        return [
            s
            for s in self._active_signals.values()
            if s.fixture_id == fixture_id and s.status == SignalStatus.ACTIVE
        ]

    async def update(self, signal: Signal) -> None:
        """Update a signal."""
        self._active_signals[signal.id] = signal
        logger.debug(f"Updated signal {signal.id}")

    async def delete(self, signal_id: str) -> bool:
        """Delete a signal."""
        if signal_id in self._active_signals:
            del self._active_signals[signal_id]
            return True
        return False

    async def save_history(self, record: SignalHistory) -> None:
        """Save a history record."""
        record.id = self._next_history_id
        self._next_history_id += 1
        sig_id = record.signal_id
        if sig_id not in self._history:
            self._history[sig_id] = []
        self._history[sig_id].append(record)

    async def get_history(self, signal_id: str) -> list[SignalHistory]:
        """Get history for a signal."""
        return list(self._history.get(signal_id, []))

    async def get_all_active(self) -> list[Signal]:
        """Get all active signals."""
        return [
            s for s in self._active_signals.values() if s.status == SignalStatus.ACTIVE
        ]

    def __len__(self) -> int:
        return len(self._active_signals)
