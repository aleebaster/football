"""xG analyzer - placeholder for expected goals data."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class XGAnalyzer(BaseAnalyzer):
    """Placeholder for xG analysis (needs real xG data source)."""

    def __init__(self) -> None:
        super().__init__("xg")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        features.set_feature("home_xg", 0.0, self._make_source(0.0))
        features.set_feature("away_xg", 0.0, self._make_source(0.0))
        features.set_feature("home_xga", 0.0, self._make_source(0.0))
        features.set_feature("away_xga", 0.0, self._make_source(0.0))
        return features
