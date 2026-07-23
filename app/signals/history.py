"""Signal History — stores signals for backtesting and tracking."""

from datetime import UTC, datetime

from app.logging import get_logger
from app.signals.models import Signal, SignalHistory

logger = get_logger(__name__)


class SignalHistoryStore:
    """In-memory signal history store.

    Ready for database persistence when needed.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[SignalHistory]] = {}  # signal_id -> records
        self._next_id = 1

    async def store(self, signal: Signal) -> SignalHistory:
        """Store a signal in history.

        Args:
            signal: Signal to store.

        Returns:
            Stored signal history record.
        """
        record = SignalHistory(
            id=self._next_id,
            signal_id=signal.id,
            fixture_id=signal.fixture_id,
            signal=signal,
        )
        self._next_id += 1

        if signal.id not in self._history:
            self._history[signal.id] = []
        self._history[signal.id].append(record)

        logger.debug(f"Stored signal {signal.id} in history")
        return record

    async def get_latest(self, signal_id: str) -> SignalHistory | None:
        """Get the most recent record for a signal.

        Args:
            signal_id: Signal ID to look up.

        Returns:
            Most recent history record or None.
        """
        records = self._history.get(signal_id, [])
        return records[-1] if records else None

    async def get_all(self, signal_id: str) -> list[SignalHistory]:
        """Get all records for a signal.

        Args:
            signal_id: Signal ID to look up.

        Returns:
            List of history records.
        """
        return list(self._history.get(signal_id, []))

    async def get_by_fixture(self, fixture_id: int) -> list[SignalHistory]:
        """Get all signals for a fixture.

        Args:
            fixture_id: Fixture ID to look up.

        Returns:
            List of history records.
        """
        all_records = []
        for records in self._history.values():
            for record in records:
                if record.fixture_id == fixture_id:
                    all_records.append(record)
        return all_records

    async def get_completed(self) -> list[SignalHistory]:
        """Get all completed signal history records (where outcome is known).

        Returns:
            List of completed signal history records.
        """
        completed = []
        for records in self._history.values():
            for record in records:
                if record.actual_outcome is not None:
                    completed.append(record)
        return completed

    async def record_outcome(
        self,
        signal_id: str,
        outcome: str,
    ) -> None:
        """Record the actual outcome for a signal.

        Args:
            signal_id: Signal ID.
            outcome: Actual outcome.
        """
        records = self._history.get(signal_id, [])
        if not records:
            return

        latest = records[-1]
        latest.actual_outcome = outcome
        latest.resolved_at = datetime.now(UTC)

        # Check if prediction was correct
        if latest.signal.outcome and latest.signal.outcome == outcome:
            latest.is_correct = True
        else:
            latest.is_correct = False

        logger.info(
            f"Recorded outcome for signal {signal_id}: {outcome}, "
            f"correct={latest.is_correct}"
        )

    async def get_accuracy(self, signal_ids: list[str] | None = None) -> float:
        """Calculate prediction accuracy.

        Args:
            signal_ids: Optional list of signal IDs to filter by.

        Returns:
            Accuracy as a float between 0 and 1.
        """
        all_records = []
        for sig_id, records in self._history.items():
            if signal_ids is None or sig_id in signal_ids:
                all_records.extend(records)

        completed = [r for r in all_records if r.is_correct is not None]
        if not completed:
            return 0.0

        correct = sum(1 for r in completed if r.is_correct)
        return correct / len(completed)

    async def get_roi(self) -> float:
        """Calculate overall ROI.

        Returns:
            ROI as a float.
        """
        all_records = []
        for records in self._history.values():
            all_records.extend(records)

        completed = [r for r in all_records if r.is_correct is not None]
        if not completed:
            return 0.0

        total_roi = sum(r.roi for r in completed)
        return total_roi / len(completed) if completed else 0.0

    async def get_all_records(self) -> list[SignalHistory]:
        """Get all history records across all signals.

        Returns:
            List of all history records.
        """
        all_records = []
        for records in self._history.values():
            all_records.extend(records)
        return all_records

    async def get_records_by_ids(self, signal_ids: list[str]) -> list[SignalHistory]:
        """Get history records for specific signal IDs.

        Args:
            signal_ids: List of signal IDs to look up.

        Returns:
            List of matching history records.
        """
        result: list[SignalHistory] = []
        for sig_id in signal_ids:
            result.extend(self._history.get(sig_id, []))
        return result

    def __len__(self) -> int:
        return sum(len(records) for records in self._history.values())
