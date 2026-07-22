"""Suspensions analyzer - placeholder for suspension data."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class SuspensionsAnalyzer(BaseAnalyzer):
    """Placeholder for suspension data analysis (needs real data source)."""

    def __init__(self) -> None:
        super().__init__("suspensions")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        features.set_feature("home_suspensions", 0, self._make_source(0.0))
        features.set_feature("away_suspensions", 0, self._make_source(0.0))
        return features
