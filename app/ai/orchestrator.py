"""AI Orchestrator - coordinates the full analysis pipeline."""

import time
from typing import Any

from app.ai.confidence import ConfidenceEngine
from app.ai.exceptions import AIEngineError
from app.ai.explainability import ExplainabilityEngine
from app.ai.feature_pipeline import FeaturePipeline
from app.ai.feature_store import FeatureStore
from app.ai.models import (
    AnalysisContext,
    AnalysisRequest,
    AnalysisResult,
    AnalysisStatus,
    PredictionContext,
    RuleResult,
)
from app.ai.registry import AnalyzerRegistry
from app.ai.rules import RuleEngine
from app.ai.validation import ValidationEngine
from app.logging import get_logger
from app.providers.manager import ProviderManager

logger = get_logger(__name__)


class AIOrchestrator:
    """Coordinates the full analysis pipeline.

    Pipeline: Fetch Data → Validate → Extract Features → Run Rules →
              Calculate Confidence → Generate Explanation → Build Result
    """

    def __init__(
        self,
        provider_manager: ProviderManager,
        pipeline: FeaturePipeline,
        rule_engine: RuleEngine,
        confidence_engine: ConfidenceEngine,
        explainability_engine: ExplainabilityEngine,
        validation_engine: ValidationEngine,
        feature_store: FeatureStore,
        registry: AnalyzerRegistry,
    ) -> None:
        self._pm = provider_manager
        self._pipeline = pipeline
        self._rules = rule_engine
        self._confidence = confidence_engine
        self._explain = explainability_engine
        self._validation = validation_engine
        self._feature_store = feature_store
        self._registry = registry

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Run full match analysis."""
        start = time.perf_counter()

        # Validate request
        self._validation.validate_request(request)

        try:
            # Step 1: Fetch data from providers
            context = await self._fetch_data(request)

            # Step 2: Validate context
            self._validation.validate_context(context)

            # Step 3: Run feature pipeline
            features, analyzers_used = await self._pipeline.run(
                context, request.analyzers
            )

            # Step 4: Cache features
            await self._feature_store.set(request.fixture_id, features.features)

            # Step 5: Run rules
            rule_results = self._rules.evaluate(features)

            # Step 6: Calculate confidence
            confidence, risk = self._confidence.calculate(features, rule_results)

            # Step 7: Generate explanation
            explanation = self._explain.explain(features, rule_results)

            # Step 8: Build prediction context
            prediction = self._build_prediction(
                request, features, rule_results, confidence, risk
            )

            elapsed = (time.perf_counter() - start) * 1000

            result = AnalysisResult(
                fixture_id=request.fixture_id,
                home_team_id=request.home_team_id,
                away_team_id=request.away_team_id,
                status=AnalysisStatus.SUCCESS,
                prediction=prediction,
                features=features,
                rules=rule_results,
                confidence=confidence,
                risk=risk,
                explanation=explanation,
                analyzers_used=analyzers_used,
                analysis_time_ms=round(elapsed, 2),
            )

            logger.info(
                f"Analysis complete for fixture {request.fixture_id} "
                f"in {elapsed:.1f}ms ({len(analyzers_used)} analyzers, "
                f"{len(rule_results)} rules)"
            )
            return result

        except AIEngineError:
            raise
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"Analysis failed for fixture {request.fixture_id}: {e}")
            return AnalysisResult(
                fixture_id=request.fixture_id,
                home_team_id=request.home_team_id,
                away_team_id=request.away_team_id,
                status=AnalysisStatus.FAILED,
                analysis_time_ms=round(elapsed, 2),
            )

    async def _fetch_data(self, request: AnalysisRequest) -> AnalysisContext:
        """Fetch all required data from provider layer."""
        context = AnalysisContext(
            fixture_id=request.fixture_id,
            home_team_id=request.home_team_id,
            away_team_id=request.away_team_id,
            competition_id=request.competition_id,
        )

        # Fetch fixture
        try:
            context.fixture_data = await self._pm.fixture(request.fixture_id)
        except Exception as e:
            logger.warning(f"Failed to fetch fixture: {e}")

        # Fetch standings
        if request.competition_id:
            try:
                standings = await self._pm.standings(request.competition_id)
                for s in standings:
                    if s.team_id == request.home_team_id:
                        context.home_standings = s
                    elif s.team_id == request.away_team_id:
                        context.away_standings = s
            except Exception as e:
                logger.warning(f"Failed to fetch standings: {e}")

        # Fetch recent fixtures for both teams
        try:
            context.home_fixtures = await self._pm.fixtures(
                team_id=request.home_team_id, limit=10
            )
        except Exception as e:
            logger.warning(f"Failed to fetch home fixtures: {e}")

        try:
            context.away_fixtures = await self._pm.fixtures(
                team_id=request.away_team_id, limit=10
            )
        except Exception as e:
            logger.warning(f"Failed to fetch away fixtures: {e}")

        # Fetch H2H
        try:
            context.head_to_head = await self._pm.head_to_head(
                request.home_team_id, request.away_team_id
            )
        except Exception as e:
            logger.warning(f"Failed to fetch H2H: {e}")

        # Fetch odds
        try:
            context.odds = await self._pm.odds(request.fixture_id)
        except Exception as e:
            logger.warning(f"Failed to fetch odds: {e}")

        # Fetch statistics
        try:
            stats = await self._pm.statistics(request.fixture_id)
            if stats:
                context.statistics = {"raw": stats}
        except Exception as e:
            logger.warning(f"Failed to fetch statistics: {e}")

        return context

    def _build_prediction(
        self,
        request: AnalysisRequest,
        features: Any,
        rules: list[RuleResult],
        confidence: Any,
        risk: Any,
    ) -> PredictionContext:
        """Build prediction from rule results."""
        from app.ai.models import MatchOutcome

        home_score = sum(
            r.weight * r.impact for r in rules if r.outcome == MatchOutcome.HOME_WIN
        )
        away_score = sum(
            r.weight * r.impact for r in rules if r.outcome == MatchOutcome.AWAY_WIN
        )
        draw_score = sum(
            r.weight * r.impact for r in rules if r.outcome == MatchOutcome.DRAW
        )

        # Convert scores to probabilities via softmax with overflow protection
        import math

        raw = [home_score + 0.5, draw_score + 0.3, away_score + 0.5]
        max_r = max(raw)
        # Clamp to avoid overflow: exp(x) safe when x <= 20
        exps = [math.exp(min(r - max_r, 20.0)) for r in raw]
        total_exp = sum(exps) or 1.0

        probs = [e / total_exp for e in exps]

        return PredictionContext(
            fixture_id=request.fixture_id,
            home_team_id=request.home_team_id,
            away_team_id=request.away_team_id,
            features=features.features if hasattr(features, "features") else {},
            probability_home=round(probs[0], 3),
            probability_draw=round(probs[1], 3),
            probability_away=round(probs[2], 3),
            confidence=confidence,
            risk=risk,
        )
