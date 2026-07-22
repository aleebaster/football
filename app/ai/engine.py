"""AI Engine - main entry point for the AI Analysis Engine."""

from app.ai.cache import AIAnalysisCache
from app.ai.confidence import ConfidenceEngine
from app.ai.explainability import ExplainabilityEngine
from app.ai.feature_pipeline import FeaturePipeline
from app.ai.feature_store import FeatureStore
from app.ai.models import AnalysisRequest, AnalysisResult
from app.ai.orchestrator import AIOrchestrator
from app.ai.registry import AnalyzerRegistry
from app.ai.rules import RuleEngine
from app.ai.validation import ValidationEngine
from app.cache.base import CacheManager
from app.logging import get_logger
from app.providers.manager import ProviderManager

logger = get_logger(__name__)


class AIEngine:
    """Main AI Engine - coordinates all AI analysis components.

    Usage:
        engine = AIEngine(provider_manager, cache_manager)
        result = await engine.analyze(analysis_request)
    """

    def __init__(
        self,
        provider_manager: ProviderManager,
        cache_manager: CacheManager,
    ) -> None:
        self._provider_manager = provider_manager
        self._cache_manager = cache_manager

        # Initialize components
        self._registry = AnalyzerRegistry()
        self._register_analyzers()

        self._feature_store = FeatureStore(cache_manager)
        self._analysis_cache = AIAnalysisCache(cache_manager)
        self._pipeline = FeaturePipeline(self._registry)
        self._rule_engine = RuleEngine()
        self._confidence_engine = ConfidenceEngine()
        self._explainability_engine = ExplainabilityEngine()
        self._validation_engine = ValidationEngine()

        self._orchestrator = AIOrchestrator(
            provider_manager=provider_manager,
            pipeline=self._pipeline,
            rule_engine=self._rule_engine,
            confidence_engine=self._confidence_engine,
            explainability_engine=self._explainability_engine,
            validation_engine=self._validation_engine,
            feature_store=self._feature_store,
            registry=self._registry,
        )

        logger.info(
            f"AI Engine initialized with {len(self._registry)} analyzers "
            f"and {len(self._rule_engine)} rules"
        )

    def _register_analyzers(self) -> None:
        """Register all built-in analyzers."""
        from app.ai.analyzers import ALL_ANALYZERS

        for analyzer_cls in ALL_ANALYZERS:
            self._registry.register(analyzer_cls())  # type: ignore[abstract]

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyze a match.

        Checks cache first, then runs full analysis pipeline.
        """
        # Check cache
        if not request.force_refresh:
            cached = await self._analysis_cache.get(request.fixture_id)
            if cached is not None:
                logger.debug(
                    f"Returning cached analysis for fixture {request.fixture_id}"
                )
                return AnalysisResult(**cached)

        # Run analysis
        result = await self._orchestrator.analyze(request)

        # Cache result
        if result.status.value == "success":
            try:
                await self._analysis_cache.set(
                    request.fixture_id,
                    result.model_dump(mode="json"),
                )
            except Exception as e:
                logger.warning(f"Failed to cache analysis: {e}")

        return result

    @property
    def registry(self) -> AnalyzerRegistry:
        return self._registry

    @property
    def rule_engine(self) -> RuleEngine:
        return self._rule_engine

    def __len__(self) -> int:
        return len(self._registry)
