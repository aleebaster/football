"""Goals analyzer - goal-scoring and conceding patterns."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class GoalsAnalyzer(BaseAnalyzer):
    """Analyzes goal-scoring patterns for both teams."""

    def __init__(self) -> None:
        super().__init__("goals")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        hgf = features.get("home_goals_for", 0)
        hga = features.get("home_goals_against", 0)
        agf = features.get("away_goals_for", 0)
        aga = features.get("away_goals_against", 0)
        hp = features.get("home_played", 1) or 1
        ap = features.get("away_played", 1) or 1

        features.set_feature("home_avg_scored", hgf / hp, self._make_source())
        features.set_feature("home_avg_conceded", hga / hp, self._make_source())
        features.set_feature("away_avg_scored", agf / ap, self._make_source())
        features.set_feature("away_avg_conceded", aga / ap, self._make_source())
        features.set_feature(
            "home_goal_diff_per_game", (hgf - hga) / hp, self._make_source()
        )
        features.set_feature(
            "away_goal_diff_per_game", (agf - aga) / ap, self._make_source()
        )
        features.set_feature(
            "total_expected_goals",
            (hgf / hp + aga / ap + agf / ap + hga / hp) / 2,
            self._make_source(),
        )
        return features
