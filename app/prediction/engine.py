"""Prediction Engine — main entry point for match predictions.

Works exclusively through the AI Analysis Engine:
    Provider Layer → AI Engine → Prediction Engine → Telegram / Dashboard
"""

from app.ai.engine import AIEngine
from app.cache.base import CacheManager
from app.logging import get_logger
from app.prediction.cache import PredictionCache
from app.prediction.calibration import CalibrationEngine
from app.prediction.consensus import ConsensusEngine
from app.prediction.history import PredictionHistoryStore
from app.prediction.models import PredictionRequest, PredictionResult, PredictionSummary
from app.prediction.orchestrator import PredictionOrchestrator
from app.prediction.registry import PredictorRegistry
from app.prediction.risk import RiskEngine
from app.prediction.validator import PredictionValidator
from app.prediction.value import ValueBetEngine

logger = get_logger(__name__)


class PredictionEngine:
    """Main entry point for the Prediction Engine.

    Usage:
        engine = PredictionEngine(ai_engine, cache_manager)
        result = await engine.predict(prediction_request)
    """

    def __init__(
        self,
        ai_engine: AIEngine,
        cache_manager: CacheManager,
    ) -> None:
        self._ai_engine = ai_engine
        self._cache = PredictionCache(cache_manager)

        # Initialize components
        self._registry = PredictorRegistry()
        self._register_predictors()

        self._consensus = ConsensusEngine()
        self._risk = RiskEngine()
        self._value = ValueBetEngine()
        self._calibration = CalibrationEngine()
        self._validator = PredictionValidator()
        self._history = PredictionHistoryStore()

        self._orchestrator = PredictionOrchestrator(
            ai_engine=ai_engine,
            registry=self._registry,
            consensus=self._consensus,
            risk_engine=self._risk,
            value_engine=self._value,
            calibration=self._calibration,
            validator=self._validator,
            history=self._history,
        )

        logger.info(f"Prediction Engine initialized with {len(self._registry)} markets")

    def _register_predictors(self) -> None:
        """Register all built-in predictors."""
        from app.prediction.predictors.asian_handicap import AsianHandicapPredictor
        from app.prediction.predictors.btts import BTTSPredictor
        from app.prediction.predictors.cards import CardsPredictor
        from app.prediction.predictors.corners import CornersPredictor
        from app.prediction.predictors.double_chance import DoubleChancePredictor
        from app.prediction.predictors.first_goal import FirstGoalPredictor
        from app.prediction.predictors.halftime import HalftimePredictor
        from app.prediction.predictors.over_under import OverUnderPredictor
        from app.prediction.predictors.winner import WinnerPredictor

        for predictor in [
            WinnerPredictor(),
            DoubleChancePredictor(),
            OverUnderPredictor(),
            BTTSPredictor(),
            AsianHandicapPredictor(),
            CornersPredictor(),
            CardsPredictor(),
            FirstGoalPredictor(),
            HalftimePredictor(),
        ]:
            self._registry.register(predictor)

    async def predict(self, request: PredictionRequest) -> PredictionResult:
        """Generate prediction for a match.

        Checks cache first, then runs full pipeline.
        """
        if not request.force_refresh:
            cached = await self._cache.get(request.fixture_id)
            if cached is not None:
                logger.debug(
                    f"Returning cached prediction for fixture {request.fixture_id}"
                )
                return PredictionResult.model_validate(cached)

        result = await self._orchestrator.predict(request)

        # Cache result
        try:
            await self._cache.set(
                request.fixture_id,
                result.model_dump(mode="json"),
            )
        except Exception as e:
            logger.warning(f"Failed to cache prediction: {e}")

        return result

    async def get_summary(self, request: PredictionRequest) -> PredictionSummary:
        """Get lightweight prediction summary."""
        return await self._orchestrator.get_summary(request)

    @property
    def history(self) -> PredictionHistoryStore:
        return self._history

    @property
    def registry(self) -> PredictorRegistry:
        return self._registry

    def __len__(self) -> int:
        return len(self._registry)
