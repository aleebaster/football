"""Head-to-head analyzer."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class H2HAnalyzer(BaseAnalyzer):
    """Analyzes head-to-head history between two teams."""

    def __init__(self) -> None:
        super().__init__("h2h")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        h2h = context.head_to_head
        if not h2h:
            features.set_feature("h2h_available", False, self._make_source(0.0))
            return features

        features.set_feature("h2h_available", True, self._make_source())
        features.set_feature("h2h_matches", len(h2h), self._make_source())

        home_wins = 0
        away_wins = 0
        draws = 0
        home_goals = 0
        away_goals = 0

        for match in h2h:
            if hasattr(match, "home_score") and match.home_score is not None:
                hs, as_ = match.home_score, match.away_score
                home_goals += hs
                away_goals += as_
                if hs > as_:
                    if match.home_team_id == context.home_team_id:
                        home_wins += 1
                    else:
                        away_wins += 1
                elif as_ > hs:
                    if match.away_team_id == context.home_team_id:
                        home_wins += 1
                    else:
                        away_wins += 1
                else:
                    draws += 1

        total = len(h2h) or 1
        features.set_feature(
            "h2h_home_win_rate", home_wins / total, self._make_source()
        )
        features.set_feature(
            "h2h_away_win_rate", away_wins / total, self._make_source()
        )
        features.set_feature("h2h_draw_rate", draws / total, self._make_source())
        features.set_feature(
            "h2h_avg_home_goals", home_goals / total, self._make_source()
        )
        features.set_feature(
            "h2h_avg_away_goals", away_goals / total, self._make_source()
        )
        features.set_feature(
            "h2h_advantage",
            (home_wins - away_wins) / total,
            self._make_source(),
        )
        return features
