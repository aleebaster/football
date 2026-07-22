"""Prediction History — stores predictions for backtesting and tracking."""

from app.logging import get_logger
from app.prediction.models import PredictionHistory, PredictionResult

logger = get_logger(__name__)


class PredictionHistoryStore:
    """In-memory prediction history store.

    Ready for database persistence when needed.
    """

    def __init__(self) -> None:
        self._history: dict[int, list[PredictionHistory]] = {}
        self._next_id = 1

    async def store(self, prediction: PredictionResult) -> PredictionHistory:
        """Store a prediction result."""
        record = PredictionHistory(
            id=self._next_id,
            fixture_id=prediction.fixture_id,
            prediction=prediction,
        )
        self._next_id += 1

        if prediction.fixture_id not in self._history:
            self._history[prediction.fixture_id] = []
        self._history[prediction.fixture_id].append(record)

        logger.debug(f"Stored prediction for fixture {prediction.fixture_id}")
        return record

    async def get_latest(self, fixture_id: int) -> PredictionHistory | None:
        """Get the most recent prediction for a fixture."""
        records = self._history.get(fixture_id, [])
        return records[-1] if records else None

    async def get_all(self, fixture_id: int) -> list[PredictionHistory]:
        """Get all predictions for a fixture."""
        return list(self._history.get(fixture_id, []))

    async def record_outcome(
        self,
        fixture_id: int,
        outcome: str,
    ) -> None:
        """Record the actual outcome for a fixture (for backtesting)."""
        records = self._history.get(fixture_id, [])
        if not records:
            return

        latest = records[-1]
        latest.actual_outcome = outcome

        # Check if prediction was correct
        if latest.prediction.predictions:
            winner_market = latest.prediction.predictions[0]
            if winner_market.distribution.primary_outcome[0] == outcome:
                latest.is_correct = True
            else:
                latest.is_correct = False

        logger.info(
            f"Recorded outcome for fixture {fixture_id}: {outcome}, "
            f"correct={latest.is_correct}"
        )

    async def get_accuracy(self, fixture_ids: list[int] | None = None) -> float:
        """Calculate prediction accuracy."""
        all_records = []
        for fid, records in self._history.items():
            if fixture_ids is None or fid in fixture_ids:
                all_records.extend(records)

        completed = [r for r in all_records if r.is_correct is not None]
        if not completed:
            return 0.0

        correct = sum(1 for r in completed if r.is_correct)
        return correct / len(completed)

    def __len__(self) -> int:
        return sum(len(records) for records in self._history.values())
