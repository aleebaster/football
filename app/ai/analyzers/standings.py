"""Standings analyzer - league table analysis."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class StandingsAnalyzer(BaseAnalyzer):
    """Analyzes league standings for both teams."""

    def __init__(self) -> None:
        super().__init__("standings")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        completeness = 0.0

        if context.home_standings:
            home = context.home_standings
            features.set_feature("home_position", home.position, self._make_source())
            features.set_feature("home_points", home.points, self._make_source())
            features.set_feature("home_played", home.played, self._make_source())
            features.set_feature("home_won", home.won, self._make_source())
            features.set_feature("home_drawn", home.draw, self._make_source())
            features.set_feature("home_lost", home.lost, self._make_source())
            features.set_feature("home_goals_for", home.goals_for, self._make_source())
            features.set_feature(
                "home_goals_against", home.goals_against, self._make_source()
            )
            if home.played > 0:
                features.set_feature(
                    "home_ppg", home.points / home.played, self._make_source()
                )
                features.set_feature(
                    "home_gpg", home.goals_for / home.played, self._make_source()
                )
            completeness += 0.5

        if context.away_standings:
            away = context.away_standings
            features.set_feature("away_position", away.position, self._make_source())
            features.set_feature("away_points", away.points, self._make_source())
            features.set_feature("away_played", away.played, self._make_source())
            features.set_feature("away_won", away.won, self._make_source())
            features.set_feature("away_drawn", away.draw, self._make_source())
            features.set_feature("away_lost", away.lost, self._make_source())
            features.set_feature("away_goals_for", away.goals_for, self._make_source())
            features.set_feature(
                "away_goals_against", away.goals_against, self._make_source()
            )
            if away.played > 0:
                features.set_feature(
                    "away_ppg", away.points / away.played, self._make_source()
                )
                features.set_feature(
                    "away_gpg", away.goals_for / away.played, self._make_source()
                )
            completeness += 0.5

        hp = features.get("home_position")
        ap = features.get("away_position")
        if hp is not None and ap is not None:
            features.set_feature(
                "standings_advantage", (ap - hp) / 20.0, self._make_source()
            )

        features.set_feature(
            "standings_data_completeness", completeness, self._make_source()
        )
        return features
