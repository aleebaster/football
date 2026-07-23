"""Backtesting Dataset — loads historical match data for backtesting."""

from typing import Any

from app.backtesting.exceptions import BacktestDatasetError
from app.backtesting.models import BacktestRequest, BacktestScope
from app.logging import get_logger
from app.providers.manager import ProviderManager

logger = get_logger(__name__)


class BacktestDataset:
    """Loads historical match data for backtesting.

    Uses the Provider Layer to fetch historical data.
    Raises BacktestDatasetError when no provider is available.
    """

    def __init__(self, provider_manager: ProviderManager | None = None) -> None:
        self._provider_manager = provider_manager
        self._cache: dict[int, dict[str, Any]] = {}

    async def load(self, request: BacktestRequest) -> list[dict[str, Any]]:
        """Load historical match data based on request scope.

        Args:
            request: Backtest request with scope parameters.

        Returns:
            List of historical match data dictionaries.

        Raises:
            BacktestDatasetError: If data loading fails.
        """
        try:
            matches = await self._fetch_matches(request)
            logger.info(
                f"Loaded {len(matches)} matches for scope={request.scope.value}"
            )
            return matches
        except BacktestDatasetError:
            raise
        except Exception as e:
            raise BacktestDatasetError(f"Failed to load dataset: {e}") from e

    async def get_match(self, fixture_id: int) -> dict[str, Any] | None:
        """Get a specific historical match by fixture ID."""
        if fixture_id in self._cache:
            return self._cache[fixture_id]

        if self._provider_manager is None:
            raise BacktestDatasetError("No provider available for fetching match data")

        try:
            fixture = await self._provider_manager.fixture(fixture_id)
            if fixture is None:
                return None
            match_data = fixture.model_dump()
            self._cache[fixture_id] = match_data
            return match_data
        except Exception as e:
            logger.warning(f"Failed to fetch fixture {fixture_id}: {e}")
            return None

    async def count(self, request: BacktestRequest) -> int:
        """Count matches in the dataset for a request."""
        matches = await self.load(request)
        return len(matches)

    async def _fetch_matches(self, request: BacktestRequest) -> list[dict[str, Any]]:
        """Fetch matches based on scope."""
        if self._provider_manager is None:
            raise BacktestDatasetError(
                "No provider manager available. "
                "Register a provider before running backtests."
            )

        if request.scope == BacktestScope.SINGLE_MATCH:
            match = await self.get_match(request.fixture_id or 0)
            return [match] if match else []

        if request.scope == BacktestScope.LEAGUE:
            fixtures = await self._provider_manager.fixtures(
                competition_id=request.league_id,
                limit=request.max_matches,
            )
            return [f.model_dump() for f in fixtures]

        if request.scope == BacktestScope.DATE_RANGE:
            fixtures = await self._provider_manager.fixtures(
                date_from=request.date_from,
                date_to=request.date_to,
                limit=request.max_matches,
            )
            return [f.model_dump() for f in fixtures]

        if request.scope == BacktestScope.SEASON:
            fixtures = await self._provider_manager.fixtures(
                competition_id=request.league_id,
                limit=request.max_matches,
            )
            return [f.model_dump() for f in fixtures]

        # Default: fetch recent fixtures
        fixtures = await self._provider_manager.fixtures(limit=request.max_matches)
        return [f.model_dump() for f in fixtures]
