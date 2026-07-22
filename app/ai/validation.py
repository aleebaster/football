"""Validation module - validates data quality before analysis."""

from app.ai.exceptions import InsufficientDataError, ValidationError
from app.ai.models import AnalysisContext, AnalysisRequest
from app.logging import get_logger

logger = get_logger(__name__)


class ValidationEngine:
    """Validates data completeness and quality before analysis."""

    def validate_request(self, request: AnalysisRequest) -> None:
        """Validate the analysis request."""
        if request.fixture_id <= 0:
            raise ValidationError("Invalid fixture_id")
        if request.home_team_id <= 0:
            raise ValidationError("Invalid home_team_id")
        if request.away_team_id <= 0:
            raise ValidationError("Invalid away_team_id")
        if request.home_team_id == request.away_team_id:
            raise ValidationError("Home and away teams must be different")

    def validate_context(self, context: AnalysisContext) -> list[str]:
        """Validate analysis context and return warnings.

        Returns list of warnings rather than raising, since partial data
        is acceptable for degraded analysis.
        """
        warnings: list[str] = []

        if context.fixture_data is None:
            warnings.append("No fixture data available")

        if context.home_standings is None:
            warnings.append("No home team standings")

        if context.away_standings is None:
            warnings.append("No away team standings")

        if not context.home_fixtures:
            warnings.append("No recent home team fixtures")

        if not context.away_fixtures:
            warnings.append("No recent away team fixtures")

        if not context.head_to_head:
            warnings.append("No head-to-head data")

        # Critical: need at least some data
        data_count = sum(
            [
                1 if context.fixture_data else 0,
                1 if context.home_standings else 0,
                1 if context.away_standings else 0,
                1 if context.home_fixtures else 0,
                1 if context.away_fixtures else 0,
            ]
        )

        if data_count < 2:
            raise InsufficientDataError(
                "Insufficient data for analysis - at least 2 data sources required"
            )

        return warnings
