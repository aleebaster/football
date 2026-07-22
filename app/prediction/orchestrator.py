"""Prediction Orchestrator — coordinates the full prediction pipeline."""

import time
from typing import Any

from app.ai.engine import AIEngine
from app.ai.models import AnalysisRequest, AnalysisResult
from app.logging import get_logger
from app.prediction.calibration import CalibrationEngine
from app.prediction.consensus import ConsensusEngine
from app.prediction.history import PredictionHistoryStore
from app.prediction.models import (
    MarketPrediction,
    PredictionExplanation,
    PredictionRequest,
    PredictionResult,
    PredictionSummary,
)
from app.prediction.registry import PredictorRegistry
from app.prediction.risk import RiskEngine
from app.prediction.validator import PredictionValidator
from app.prediction.value import ValueBetEngine

logger = get_logger(__name__)


class PredictionOrchestrator:
    """Coordinates: AI Analysis → Predictor → Consensus → Risk → Value → Result."""

    def __init__(
        self,
        ai_engine: AIEngine,
        registry: PredictorRegistry,
        consensus: ConsensusEngine,
        risk_engine: RiskEngine,
        value_engine: ValueBetEngine,
        calibration: CalibrationEngine,
        validator: PredictionValidator,
        history: PredictionHistoryStore,
    ) -> None:
        self._ai = ai_engine
        self._registry = registry
        self._consensus = consensus
        self._risk = risk_engine
        self._value = value_engine
        self._calibration = calibration
        self._validator = validator
        self._history = history

    async def predict(self, request: PredictionRequest) -> PredictionResult:
        """Run full prediction pipeline."""
        start = time.perf_counter()

        # Step 1: Run AI Analysis Engine
        analysis_request = AnalysisRequest(
            fixture_id=request.fixture_id,
            home_team_id=request.home_team_id,
            away_team_id=request.away_team_id,
            competition_id=request.competition_id,
            force_refresh=request.force_refresh,
        )
        analysis = await self._ai.analyze(analysis_request)

        # Step 2: Validate
        self._validator.validate(analysis)

        # Step 3: Determine markets
        markets = request.markets or list(self._registry.get_supported_markets())

        # Step 4: Run predictors
        predictions: list[MarketPrediction] = []
        features = analysis.features.features if analysis.features else {}
        odds_data = self._extract_odds(analysis)

        for market in markets:
            predictor = self._registry.get(market)
            if predictor is None:
                continue
            try:
                pred = await predictor.predict(features, odds_data)
                # Apply calibration
                pred.distribution = self._calibration.calibrate(pred.distribution)
                predictions.append(pred)
            except Exception as e:
                logger.warning(f"Predictor {market.value} failed: {e}")

        # Step 5: Consensus
        consensus = self._consensus.aggregate(analysis)

        # Step 6: Overall risk
        risk = self._risk.assess(analysis)

        # Step 7: Overall confidence
        overall_confidence = analysis.confidence.overall if analysis.confidence else 0.5

        # Step 8: Value bets
        for pred in predictions:
            if odds_data and odds_data.get(pred.distribution.primary_outcome[0]):
                pred.value_bets = self._value.find_value(pred.distribution, odds_data)

        # Step 9: Build explanation
        explanation = self._build_explanation(predictions, consensus, analysis)

        elapsed = (time.perf_counter() - start) * 1000

        result = PredictionResult(
            fixture_id=request.fixture_id,
            home_team_id=request.home_team_id,
            away_team_id=request.away_team_id,
            predictions=predictions,
            consensus=consensus,
            overall_confidence=round(overall_confidence, 3),
            overall_risk=risk,
            explanation=explanation,
            prediction_time_ms=round(elapsed, 2),
        )

        # Step 10: Store in history
        await self._history.store(result)

        logger.info(
            f"Prediction complete for fixture {request.fixture_id} "
            f"in {elapsed:.1f}ms ({len(predictions)} markets)"
        )
        return result

    async def get_summary(self, request: PredictionRequest) -> PredictionSummary:
        """Get a lightweight prediction summary."""
        result = await self.predict(request)

        winner = result.predictions[0] if result.predictions else None
        home_pct = 0.0
        draw_pct = 0.0
        away_pct = 0.0

        if winner and winner.distribution:
            home_pct = winner.distribution.outcomes.get("home", 0) * 100
            draw_pct = winner.distribution.outcomes.get("draw", 0) * 100
            away_pct = winner.distribution.outcomes.get("away", 0) * 100

        top_value = None
        all_value = []
        for p in result.predictions:
            all_value.extend(p.value_bets)
        if all_value:
            all_value.sort(key=lambda vb: vb.edge, reverse=True)
            top_value = all_value[0]

        return PredictionSummary(
            fixture_id=result.fixture_id,
            home_team_id=result.home_team_id,
            away_team_id=result.away_team_id,
            home_win_pct=round(home_pct, 1),
            draw_pct=round(draw_pct, 1),
            away_win_pct=round(away_pct, 1),
            confidence=round(result.overall_confidence * 100, 1),
            risk_level=result.overall_risk.level,
            top_value_bet=top_value,
        )

    def _extract_odds(self, analysis: AnalysisResult) -> dict[str, float] | None:
        """Extract odds from analysis context."""
        if not analysis.features:
            return None
        features = analysis.features.features
        odds = {}
        if features.get("odds_fair_home"):
            odds["home"] = features["odds_fair_home"]
        if features.get("odds_fair_away"):
            odds["away"] = features["odds_fair_away"]
        return odds if odds else None

    def _build_explanation(
        self,
        predictions: list[MarketPrediction],
        consensus: Any,
        analysis: AnalysisResult,  # noqa: ARG002
    ) -> PredictionExplanation:
        """Build overall explanation from all predictions."""
        key_factors = list(consensus.factors) if consensus else []
        warnings: list[str] = []

        if analysis.confidence and analysis.confidence.overall < 0.3:
            warnings.append("Low confidence — prediction may be unreliable")

        if analysis.features:
            n_features = len(analysis.features.features)
            if n_features < 5:
                warnings.append(f"Limited data: only {n_features} features available")

        return PredictionExplanation(
            summary=f"Prediction based on {len(predictions)} markets with {consensus.source_count} signals",
            key_factors=key_factors,
            warnings=warnings,
        )
