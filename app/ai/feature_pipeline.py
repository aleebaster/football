"""Feature Pipeline - aggregates features from all analyzers."""

import time

from app.ai.models import AnalysisContext, FeatureVector
from app.ai.registry import AnalyzerRegistry
from app.logging import get_logger

logger = get_logger(__name__)


class FeaturePipeline:
    """Runs all analyzers and aggregates features into a single vector."""

    def __init__(self, registry: AnalyzerRegistry) -> None:
        self._registry = registry

    async def run(
        self,
        context: AnalysisContext,
        analyzers: list[str] | None = None,
    ) -> tuple[FeatureVector, list[str]]:
        """Run feature extraction pipeline.

        Args:
            context: Analysis context with all data.
            analyzers: Specific analyzers to run, or None for all.

        Returns:
            Tuple of (feature_vector, list of analyzer names used).
        """
        features = FeatureVector(
            fixture_id=context.fixture_id,
            home_team_id=context.home_team_id,
            away_team_id=context.away_team_id,
        )

        if analyzers:
            active = self._registry.get_by_names(analyzers)
        else:
            active = self._registry.get_all()

        used: list[str] = []
        for analyzer in active:
            try:
                start = time.perf_counter()
                features = await analyzer.extract(context, features)
                elapsed = (time.perf_counter() - start) * 1000
                used.append(analyzer.name)
                logger.debug(f"Analyzer {analyzer.name} completed in {elapsed:.1f}ms")
            except Exception as e:
                logger.warning(f"Analyzer {analyzer.name} failed: {e}")

        logger.info(
            f"Feature pipeline: {len(used)}/{len(active)} analyzers succeeded, "
            f"{len(features.features)} features extracted"
        )
        return features, used
