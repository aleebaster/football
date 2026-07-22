"""Injuries analyzer - placeholder for injury data."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class InjuriesAnalyzer(BaseAnalyzer):
    """Placeholder for injury data analysis (needs real data source)."""

    def __init__(self) -> None:
        super().__init__("injuries")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        features.set_feature("home_injuries_impact", 0.0, self._make_source(0.0))
        features.set_feature("away_injuries_impact", 0.0, self._make_source(0.0))
        return features
