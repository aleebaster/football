"""Backtesting Validator — validates backtest requests and configurations."""

from app.backtesting.exceptions import BacktestValidationError
from app.backtesting.models import BacktestRequest, BacktestScope
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestValidator:
    """Validates backtest requests before execution."""

    def validate_request(self, request: BacktestRequest) -> bool:
        """Validate a backtest request.

        Args:
            request: Request to validate.

        Returns:
            True if valid.

        Raises:
            BacktestValidationError: If validation fails.
        """
        # Scope-specific validation
        if request.scope == BacktestScope.SINGLE_MATCH:
            if request.fixture_id is None:
                raise BacktestValidationError(
                    "fixture_id is required for single_match scope"
                )

        if request.scope in (BacktestScope.DATE_RANGE, BacktestScope.ALL):
            if request.max_matches <= 0:
                raise BacktestValidationError("max_matches must be positive")

        if request.scope == BacktestScope.LEAGUE:
            if request.league_id is None:
                raise BacktestValidationError("league_id is required for league scope")

        if request.scope == BacktestScope.SEASON:
            if request.season is None:
                raise BacktestValidationError("season is required for season scope")

        if request.date_from and request.date_to:
            if request.date_from > request.date_to:
                raise BacktestValidationError("date_from must be before date_to")

        logger.debug(f"Backtest request validated: scope={request.scope.value}")
        return True
