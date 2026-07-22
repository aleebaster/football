"""Momentum analyzer."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class MomentumAnalyzer(BaseAnalyzer):
    """Analyzes recent momentum and goal-scoring trends."""

    def __init__(self) -> None:
        super().__init__("momentum")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        home_form = features.get("home_form", [])
        away_form = features.get("away_form", [])

        # Momentum: wins in last 3
        home_momentum = sum(1 for r in home_form[-3:] if r == "W") / 3.0
        away_momentum = sum(1 for r in away_form[-3:] if r == "W") / 3.0

        features.set_feature("home_momentum", home_momentum, self._make_source())
        features.set_feature("away_momentum", away_momentum, self._make_source())

        # Goal streak: consecutive matches with goals
        home_streak = self._goal_streak(context.home_fixtures, context.home_team_id)
        away_streak = self._goal_streak(context.away_fixtures, context.away_team_id)

        features.set_feature("home_goal_streak", home_streak, self._make_source())
        features.set_feature("away_goal_streak", away_streak, self._make_source())
        features.set_feature(
            "momentum_advantage",
            home_momentum - away_momentum,
            self._make_source(),
        )
        return features

    def _goal_streak(self, fixtures: list, team_id: int) -> int:  # type: ignore[type-arg]
        streak = 0
        for f in sorted(
            fixtures, key=lambda x: getattr(x, "utc_date", "") or "", reverse=True
        ):
            if hasattr(f, "home_score") and f.home_score is not None:
                is_home = f.home_team_id == team_id
                scored = f.home_score if is_home else f.away_score
                if scored and scored > 0:
                    streak += 1
                else:
                    break
        return streak
