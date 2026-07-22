"""Referee analyzer - placeholder for referee data."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class RefereeAnalyzer(BaseAnalyzer):
    """Placeholder for referee analysis (needs historical data)."""

    def __init__(self) -> None:
        super().__init__("referee")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        features.set_feature("referee_impact", 0.0, self._make_source(0.0))
        return features
