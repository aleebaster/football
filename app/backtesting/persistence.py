"""Backtesting Persistence — stores backtest results for future reference."""

from app.backtesting.models import BacktestResult, BacktestStatus
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestPersistence:
    """In-memory persistence for backtest results.

    Ready for database persistence when needed.
    """

    def __init__(self) -> None:
        self._results: dict[str, BacktestResult] = {}
        self._next_id = 1

    async def save(self, result: BacktestResult) -> str:
        """Save a backtest result.

        Args:
            result: Backtest result to save.

        Returns:
            ID of the saved result.
        """
        if not result.id:
            result.id = f"bt_{self._next_id}"
            self._next_id += 1

        self._results[result.id] = result
        logger.debug(f"Saved backtest result {result.id}")
        return result.id

    async def get(self, result_id: str) -> BacktestResult | None:
        """Get a backtest result by ID.

        Args:
            result_id: Result ID to look up.

        Returns:
            BacktestResult or None.
        """
        return self._results.get(result_id)

    async def get_all(self) -> list[BacktestResult]:
        """Get all saved backtest results.

        Returns:
            List of all backtest results.
        """
        return list(self._results.values())

    async def get_by_status(self, status: BacktestStatus) -> list[BacktestResult]:
        """Get results filtered by status.

        Args:
            status: Status to filter by.

        Returns:
            Filtered list of results.
        """
        return [r for r in self._results.values() if r.status == status]

    async def delete(self, result_id: str) -> bool:
        """Delete a backtest result.

        Args:
            result_id: Result ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        if result_id in self._results:
            del self._results[result_id]
            logger.debug(f"Deleted backtest result {result_id}")
            return True
        return False

    def __len__(self) -> int:
        return len(self._results)
