"""Odds analyzer - betting odds analysis."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class OddsAnalyzer(BaseAnalyzer):
    """Analyzes betting odds for implied probabilities and movement."""

    def __init__(self) -> None:
        super().__init__("odds")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        odds = context.odds
        if odds is None:
            features.set_feature("odds_available", False, self._make_source(0.0))
            return features

        features.set_feature("odds_available", True, self._make_source())

        for market in odds.markets:
            if market.name in ("Match Winner", "1X2", "Full Time Result"):
                for outcome in market.outcomes:
                    if outcome.value > 0:
                        implied = 1.0 / outcome.value
                        if outcome.name in ("1", "Home"):
                            features.set_feature(
                                "odds_implied_home", implied, self._make_source()
                            )
                        elif outcome.name in ("X", "Draw"):
                            features.set_feature(
                                "odds_implied_draw", implied, self._make_source()
                            )
                        elif outcome.name in ("2", "Away"):
                            features.set_feature(
                                "odds_implied_away", implied, self._make_source()
                            )

        ih = features.get("odds_implied_home", 0)
        id_ = features.get("odds_implied_draw", 0)
        ia = features.get("odds_implied_away", 0)
        total = ih + id_ + ia
        if total > 0:
            features.set_feature("odds_margin", total - 1.0, self._make_source())
            features.set_feature("odds_fair_home", ih / total, self._make_source())
            features.set_feature("odds_fair_draw", id_ / total, self._make_source())
            features.set_feature("odds_fair_away", ia / total, self._make_source())

        return features
