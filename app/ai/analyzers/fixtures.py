"""Fixtures analyzer - schedule density and fatigue."""

from datetime import UTC, datetime
from typing import Any

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class FixturesAnalyzer(BaseAnalyzer):
    """Analyzes fixture density and schedule fatigue."""

    def __init__(self) -> None:
        super().__init__("fixtures")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        home_n = len(context.home_fixtures)
        away_n = len(context.away_fixtures)

        features.set_feature("home_recent_matches", home_n, self._make_source())
        features.set_feature("away_recent_matches", away_n, self._make_source())

        features.set_feature(
            "home_days_rest",
            self._days_rest(context.home_fixtures),
            self._make_source(),
        )
        features.set_feature(
            "away_days_rest",
            self._days_rest(context.away_fixtures),
            self._make_source(),
        )
        return features

    def _days_rest(self, fixtures: list[Any]) -> float:
        if not fixtures:
            return 7.0
        now = datetime.now(UTC)
        for f in sorted(
            fixtures,
            key=lambda x: getattr(x, "utc_date", "") or "",
            reverse=True,
        ):
            if hasattr(f, "utc_date") and f.utc_date:
                try:
                    diff: float = float((now - f.utc_date).total_seconds() / 86400)
                    return max(diff, 1.0)
                except Exception:
                    pass
        return 7.0
