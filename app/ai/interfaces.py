"""Interfaces for AI Analysis Engine analyzers."""

from abc import ABC, abstractmethod

from app.ai.models import (
    AnalysisContext,
    FeatureSource,
    FeatureVector,
)


class BaseAnalyzer(ABC):
    """Abstract base class for all AI analyzers."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def extract(
        self,
        context: AnalysisContext,
        features: FeatureVector,
    ) -> FeatureVector:
        """Extract features from context and add them to the feature vector.

        Args:
            context: Shared analysis context with all data.
            features: Feature vector to populate.

        Returns:
            Updated feature vector.
        """
        ...

    def _make_source(
        self, completeness: float = 1.0, freshness: float = 0.0
    ) -> FeatureSource:
        return FeatureSource(
            analyzer=self._name,
            data_completeness=completeness,
            freshness_seconds=freshness,
        )
