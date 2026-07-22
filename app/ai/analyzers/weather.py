"""Weather analyzer - placeholder for weather data."""

from app.ai.interfaces import BaseAnalyzer
from app.ai.models import AnalysisContext, FeatureVector


class WeatherAnalyzer(BaseAnalyzer):
    """Placeholder for weather analysis (needs external API)."""

    def __init__(self) -> None:
        super().__init__("weather")

    async def extract(
        self, context: AnalysisContext, features: FeatureVector
    ) -> FeatureVector:
        features.set_feature("weather_impact", 0.0, self._make_source(0.0))
        return features
