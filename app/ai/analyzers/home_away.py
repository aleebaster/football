"""Home/Away analyzer - venue-based analysis."""

from typing import Any

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class HomeAwayAnalyzer(BaseAnalyzer):
    """Analyzes home vs away performance differences."""

    def __init__(self) -> None:
        super().__init__("home_away")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        home_fixtures = context.home_fixtures
        away_fixtures = context.away_fixtures

        home_home = self._filter_by_venue(
            home_fixtures, context.home_team_id, home=True
        )
        away_away = self._filter_by_venue(
            away_fixtures, context.away_team_id, home=False
        )

        home_home_pts = self._points_from_fixtures(home_home, context.home_team_id)
        away_away_pts = self._points_from_fixtures(away_away, context.away_team_id)

        n_home = len(home_home) or 1
        n_away = len(away_away) or 1

        features.set_feature(
            "home_home_ppg", home_home_pts / n_home, self._make_source()
        )
        features.set_feature(
            "away_away_ppg", away_away_pts / n_away, self._make_source()
        )
        features.set_feature(
            "venue_advantage",
            (home_home_pts / n_home - away_away_pts / n_away) / 3.0,
            self._make_source(),
        )
        return features

    def _filter_by_venue(
        self, fixtures: list[Any], team_id: int, home: bool
    ) -> list[Any]:
        result = []
        for f in fixtures:
            if hasattr(f, "home_team_id") and f.home_team_id is not None:
                if home and f.home_team_id == team_id:
                    result.append(f)
                elif not home and f.away_team_id == team_id:
                    result.append(f)
        return result

    def _points_from_fixtures(self, fixtures: list[Any], team_id: int) -> int:
        pts = 0
        for f in fixtures:
            if f.home_score is not None and f.away_score is not None:
                is_home = f.home_team_id == team_id
                if f.home_score == f.away_score:
                    pts += 1
                elif (is_home and f.home_score > f.away_score) or (
                    not is_home and f.away_score > f.home_score
                ):
                    pts += 3
        return pts
