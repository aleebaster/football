"""Form analyzer - team form analysis."""

from typing import Any

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class FormAnalyzer(BaseAnalyzer):
    """Analyzes recent form of both teams."""

    def __init__(self) -> None:
        super().__init__("form")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        home_form = self._extract_form(context.home_fixtures, context.home_team_id)
        away_form = self._extract_form(context.away_fixtures, context.away_team_id)

        features.set_feature("home_form", home_form, self._make_source())
        features.set_feature("away_form", away_form, self._make_source())

        # Points-based form (last 5 matches)
        home_points = sum(
            3 if r == "W" else 1 if r == "D" else 0 for r in home_form[-5:]
        )
        away_points = sum(
            3 if r == "W" else 1 if r == "D" else 0 for r in away_form[-5:]
        )

        features.set_feature("home_form_points", home_points, self._make_source())
        features.set_feature("away_form_points", away_points, self._make_source())
        features.set_feature(
            "form_advantage",
            (home_points - away_points) / 15.0,
            self._make_source(),
        )

        return features

    def _extract_form(self, fixtures: list[Any], team_id: int) -> list[str]:
        """Extract W/D/L form from recent fixtures."""
        results = []
        for f in fixtures:
            if hasattr(f, "home_team_id") and hasattr(f, "away_team_id"):
                is_home = f.home_team_id == team_id
                if f.home_score is not None and f.away_score is not None:
                    if f.home_score == f.away_score:
                        results.append("D")
                    elif (is_home and f.home_score > f.away_score) or (
                        not is_home and f.away_score > f.home_score
                    ):
                        results.append("W")
                    else:
                        results.append("L")
        return results
