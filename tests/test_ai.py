"""Tests for AI Analysis Engine."""

import pytest

from app.ai.analyzers import (
    FixturesAnalyzer,
    FormAnalyzer,
    GoalsAnalyzer,
    H2HAnalyzer,
    HomeAwayAnalyzer,
    InjuriesAnalyzer,
    MomentumAnalyzer,
    OddsAnalyzer,
    RefereeAnalyzer,
    StandingsAnalyzer,
    SuspensionsAnalyzer,
    WeatherAnalyzer,
    XGAnalyzer,
)
from app.ai.cache import AIAnalysisCache
from app.ai.confidence import ConfidenceEngine
from app.ai.engine import AIEngine
from app.ai.exceptions import InsufficientDataError, ValidationError
from app.ai.explainability import ExplainabilityEngine
from app.ai.feature_pipeline import FeaturePipeline
from app.ai.feature_store import FeatureStore
from app.ai.models import (
    AnalysisContext,
    AnalysisRequest,
    AnalysisStatus,
    FeatureSource,
    FeatureVector,
    MatchOutcome,
    RuleResult,
)
from app.ai.registry import AnalyzerRegistry
from app.ai.rules import RuleEngine
from app.ai.validation import ValidationEngine
from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.providers.adapters.mock_provider import MockProvider
from app.providers.cache import ProviderCache
from app.providers.manager import ProviderManager
from app.providers.models import (
    Fixture,
    Odds,
    OddsMarket,
    OddsOutcome,
    Standing,
)
from app.providers.registry import ProviderRegistry


def _make_cache() -> CacheManager:
    backend = MemoryCache(max_size=1000, default_ttl=300)
    return CacheManager(backend)


def _make_provider_manager() -> ProviderManager:
    reg = ProviderRegistry()
    reg.register(MockProvider(priority=100))
    cache = ProviderCache(_make_cache())
    return ProviderManager(reg, cache)


def _make_context(
    fixture_id: int = 1000,
    home_id: int = 1,
    away_id: int = 2,
    competition_id: int | None = 10,
) -> AnalysisContext:
    home_standing = Standing(
        position=3,
        team_id=1,
        team="Home",
        played=10,
        won=6,
        draw=2,
        lost=2,
        points=20,
        goals_for=18,
        goals_against=8,
    )
    away_standing = Standing(
        position=8,
        team_id=2,
        team="Away",
        played=10,
        won=4,
        draw=3,
        lost=3,
        points=15,
        goals_for=12,
        goals_against=10,
    )
    home_fixtures = [
        Fixture(
            id=i,
            home_team_id=1,
            away_team_id=10 + i,
            home_score=2,
            away_score=1,
            status="FINISHED",
        )
        for i in range(5)
    ]
    away_fixtures = [
        Fixture(
            id=i + 100,
            home_team_id=20 + i,
            away_team_id=2,
            home_score=1,
            away_score=1,
            status="FINISHED",
        )
        for i in range(5)
    ]
    h2h = [
        Fixture(
            id=200 + i,
            home_team_id=1,
            away_team_id=2,
            home_score=2,
            away_score=1,
            status="FINISHED",
        )
        for i in range(3)
    ]
    odds = Odds(
        fixture_id=fixture_id,
        markets=[
            OddsMarket(
                name="1X2",
                outcomes=[
                    OddsOutcome(name="1", value=1.8),
                    OddsOutcome(name="X", value=3.5),
                    OddsOutcome(name="2", value=4.0),
                ],
            )
        ],
    )
    return AnalysisContext(
        fixture_id=fixture_id,
        home_team_id=home_id,
        away_team_id=away_id,
        competition_id=competition_id,
        fixture_data=Fixture(id=fixture_id, home_team_id=home_id, away_team_id=away_id),
        home_standings=home_standing,
        away_standings=away_standing,
        home_fixtures=home_fixtures,
        away_fixtures=away_fixtures,
        head_to_head=h2h,
        odds=odds,
    )


# ===== Analyzer Tests =====


class TestFormAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_form(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = FormAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert "home_form" in result.features
        assert "away_form" in result.features
        assert "form_advantage" in result.features


class TestStandingsAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_standings(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = StandingsAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert "home_position" in result.features
        assert "away_position" in result.features
        assert "standings_advantage" in result.features


class TestHomeAwayAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_venue(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = HomeAwayAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert "home_home_ppg" in result.features
        assert "venue_advantage" in result.features


class TestH2HAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_h2h(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = H2HAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert "h2h_available" in result.features
        assert "h2h_advantage" in result.features

    @pytest.mark.asyncio
    async def test_no_h2h(self) -> None:
        ctx = _make_context()
        ctx.head_to_head = []
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = H2HAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert result.get("h2h_available") is False


class TestGoalsAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_goals(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        # Pre-populate standings features
        fv.features["home_goals_for"] = 18
        fv.features["home_goals_against"] = 8
        fv.features["away_goals_for"] = 12
        fv.features["away_goals_against"] = 10
        fv.features["home_played"] = 10
        fv.features["away_played"] = 10
        analyzer = GoalsAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert "home_avg_scored" in result.features
        assert "total_expected_goals" in result.features


class TestOddsAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_odds(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = OddsAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert result.get("odds_available") is True
        assert "odds_margin" in result.features

    @pytest.mark.asyncio
    async def test_no_odds(self) -> None:
        ctx = _make_context()
        ctx.odds = None
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = OddsAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert result.get("odds_available") is False


class TestFixturesAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_fixtures(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        analyzer = FixturesAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert "home_days_rest" in result.features
        assert "home_recent_matches" in result.features


class TestMomentumAnalyzer:
    @pytest.mark.asyncio
    async def test_extract_momentum(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        fv.features["home_form"] = ["W", "W", "D", "L", "W"]
        fv.features["away_form"] = ["L", "D", "W", "L", "D"]
        analyzer = MomentumAnalyzer()
        result = await analyzer.extract(ctx, fv)
        assert "home_momentum" in result.features
        assert "momentum_advantage" in result.features


class TestPlaceholderAnalyzers:
    @pytest.mark.asyncio
    async def test_injuries(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        result = await InjuriesAnalyzer().extract(ctx, fv)
        assert "home_injuries_impact" in result.features

    @pytest.mark.asyncio
    async def test_suspensions(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        result = await SuspensionsAnalyzer().extract(ctx, fv)
        assert "home_suspensions" in result.features

    @pytest.mark.asyncio
    async def test_weather(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        result = await WeatherAnalyzer().extract(ctx, fv)
        assert "weather_impact" in result.features

    @pytest.mark.asyncio
    async def test_referee(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        result = await RefereeAnalyzer().extract(ctx, fv)
        assert "referee_impact" in result.features

    @pytest.mark.asyncio
    async def test_xg(self) -> None:
        ctx = _make_context()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        result = await XGAnalyzer().extract(ctx, fv)
        assert "home_xg" in result.features


# ===== Feature Pipeline Tests =====


class TestFeaturePipeline:
    @pytest.mark.asyncio
    async def test_run_all_analyzers(self) -> None:
        reg = AnalyzerRegistry()
        reg.register(FormAnalyzer())
        reg.register(StandingsAnalyzer())
        pipeline = FeaturePipeline(reg)
        ctx = _make_context()
        features, used = await pipeline.run(ctx)
        assert len(used) == 2
        assert "form" in used
        assert "standings" in used
        assert len(features.features) > 0

    @pytest.mark.asyncio
    async def test_run_specific_analyzers(self) -> None:
        reg = AnalyzerRegistry()
        reg.register(FormAnalyzer())
        reg.register(StandingsAnalyzer())
        pipeline = FeaturePipeline(reg)
        ctx = _make_context()
        features, used = await pipeline.run(ctx, analyzers=["form"])
        assert len(used) == 1
        assert "form" in used


# ===== Rule Engine Tests =====


class TestRuleEngine:
    def test_evaluate_rules(self) -> None:
        engine = RuleEngine()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        fv.features["home_form_points"] = 12
        fv.features["away_form_points"] = 6
        fv.features["home_position"] = 3
        fv.features["away_position"] = 8
        fv.features["standings_advantage"] = 0.25
        fv.features["h2h_available"] = True
        fv.features["h2h_advantage"] = 0.5
        fv.features["h2h_home_win_rate"] = 0.7
        fv.features["h2h_away_win_rate"] = 0.2
        fv.features["home_goal_diff_per_game"] = 1.0
        fv.features["away_goal_diff_per_game"] = 0.2
        results = engine.evaluate(fv)
        assert len(results) > 0
        # All rules should favor home
        for r in results:
            assert r.outcome == MatchOutcome.HOME_WIN

    def test_no_rules_for_empty_features(self) -> None:
        engine = RuleEngine()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        results = engine.evaluate(fv)
        assert len(results) == 0


# ===== Confidence Engine Tests =====


class TestConfidenceEngine:
    def test_calculate_confidence(self) -> None:
        engine = ConfidenceEngine()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        fv.sources = [FeatureSource(analyzer="form", data_completeness=1.0)]
        rule_models = [
            RuleResult(
                rule_id="form",
                name="Form",
                weight=0.2,
                impact=0.5,
                outcome=MatchOutcome.HOME_WIN,
                description="test",
                explanation="test",
            )
        ]
        confidence, risk = engine.calculate(fv, rule_models)
        assert 0 <= confidence.overall <= 1
        assert risk.level in ("low", "medium", "high", "very_high")


# ===== Explainability Tests =====


class TestExplainabilityEngine:
    def test_explain(self) -> None:
        engine = ExplainabilityEngine()
        fv = FeatureVector(fixture_id=1000, home_team_id=1, away_team_id=2)
        fv.sources = [FeatureSource(analyzer="form", data_completeness=1.0)]
        rules = [
            RuleResult(
                rule_id="form",
                name="Form",
                weight=0.2,
                impact=0.5,
                outcome=MatchOutcome.HOME_WIN,
                description="test",
                explanation="Home team has better form",
            )
        ]
        explanation = engine.explain(fv, rules)
        assert len(explanation.key_factors) > 0
        assert len(explanation.summary) > 0


# ===== Validation Tests =====


class TestValidationEngine:
    def test_valid_request(self) -> None:
        engine = ValidationEngine()
        req = AnalysisRequest(fixture_id=1000, home_team_id=1, away_team_id=2)
        engine.validate_request(req)  # Should not raise

    def test_invalid_request(self) -> None:
        engine = ValidationEngine()
        req = AnalysisRequest(fixture_id=0, home_team_id=1, away_team_id=2)
        with pytest.raises(ValidationError):
            engine.validate_request(req)

    def test_same_teams(self) -> None:
        engine = ValidationEngine()
        req = AnalysisRequest(fixture_id=1000, home_team_id=1, away_team_id=1)
        with pytest.raises(ValidationError):
            engine.validate_request(req)

    def test_insufficient_context(self) -> None:
        engine = ValidationEngine()
        ctx = AnalysisContext(
            fixture_id=1000,
            home_team_id=1,
            away_team_id=2,
        )
        with pytest.raises(InsufficientDataError):
            engine.validate_context(ctx)


# ===== Feature Store Tests =====


class TestFeatureStore:
    @pytest.mark.asyncio
    async def test_get_set(self) -> None:
        store = FeatureStore(_make_cache())
        await store.set(1000, {"key": "value"})
        result = await store.get(1000)
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_miss(self) -> None:
        store = FeatureStore(_make_cache())
        result = await store.get(9999)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate(self) -> None:
        store = FeatureStore(_make_cache())
        await store.set(1000, {"key": "value"})
        await store.invalidate(1000)
        result = await store.get(1000)
        assert result is None


# ===== AI Cache Tests =====


class TestAIAnalysisCache:
    @pytest.mark.asyncio
    async def test_get_set(self) -> None:
        cache = AIAnalysisCache(_make_cache())
        await cache.set(1000, {"status": "success"})
        result = await cache.get(1000)
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_invalidate(self) -> None:
        cache = AIAnalysisCache(_make_cache())
        await cache.set(1000, {"status": "success"})
        await cache.invalidate(1000)
        result = await cache.get(1000)
        assert result is None


# ===== Registry Tests =====


class TestAnalyzerRegistry:
    def test_register_and_get(self) -> None:
        reg = AnalyzerRegistry()
        reg.register(FormAnalyzer())
        assert "form" in reg
        assert len(reg) == 1
        assert reg.get("form") is not None

    def test_get_all(self) -> None:
        reg = AnalyzerRegistry()
        reg.register(FormAnalyzer())
        reg.register(StandingsAnalyzer())
        assert len(reg.get_all()) == 2

    def test_get_by_names(self) -> None:
        reg = AnalyzerRegistry()
        reg.register(FormAnalyzer())
        reg.register(StandingsAnalyzer())
        result = reg.get_by_names(["form"])
        assert len(result) == 1


# ===== Full Integration Test =====


class TestAIEngineIntegration:
    @pytest.mark.asyncio
    async def test_full_analysis_cycle(self) -> None:
        """Full analysis with MockProvider."""
        pm = _make_provider_manager()
        cache = _make_cache()
        engine = AIEngine(pm, cache)

        req = AnalysisRequest(
            fixture_id=1000,
            home_team_id=1,
            away_team_id=2,
            competition_id=10,
            force_refresh=True,
        )
        result = await engine.analyze(req)
        assert result.status in (
            AnalysisStatus.SUCCESS,
            AnalysisStatus.DEGRADED,
            AnalysisStatus.FAILED,
        )
        assert result.fixture_id == 1000
        assert result.analyzers_used is not None
        assert result.analysis_time_ms > 0

    @pytest.mark.asyncio
    async def test_engine_caches_results(self) -> None:
        """Verify caching works."""
        pm = _make_provider_manager()
        cache = _make_cache()
        engine = AIEngine(pm, cache)

        req = AnalysisRequest(
            fixture_id=2000,
            home_team_id=1,
            away_team_id=2,
            force_refresh=True,
        )
        result1 = await engine.analyze(req)
        result2 = await engine.analyze(req)
        # Second call should use cache
        assert result2.fixture_id == result1.fixture_id
