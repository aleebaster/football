"""Tests for Prediction Engine."""

import pytest

from app.ai.engine import AIEngine
from app.ai.models import AnalysisStatus
from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.prediction.calibration import CalibrationEngine
from app.prediction.consensus import ConsensusEngine
from app.prediction.engine import PredictionEngine
from app.prediction.exceptions import InsufficientAnalysisError, LowConfidenceError
from app.prediction.history import PredictionHistoryStore
from app.prediction.models import (
    PredictionMarket,
    PredictionRequest,
    PredictionResult,
    ProbabilityDistribution,
    RiskLevel,
)
from app.prediction.probabilities import ProbabilityEngine
from app.prediction.registry import PredictorRegistry
from app.prediction.risk import RiskEngine
from app.prediction.validator import PredictionValidator
from app.prediction.value import ValueBetEngine
from app.providers.adapters.mock_provider import MockProvider
from app.providers.cache import ProviderCache
from app.providers.manager import ProviderManager
from app.providers.registry import ProviderRegistry


def _make_cache() -> CacheManager:
    return CacheManager(MemoryCache(max_size=1000, default_ttl=300))


def _make_provider_manager() -> ProviderManager:
    reg = ProviderRegistry()
    reg.register(MockProvider(priority=100))
    return ProviderManager(reg, ProviderCache(_make_cache()))


def _make_ai_engine() -> AIEngine:
    return AIEngine(_make_provider_manager(), _make_cache())


def _make_prediction_engine() -> PredictionEngine:
    return PredictionEngine(_make_ai_engine(), _make_cache())


# ===== Probability Engine Tests =====


class TestProbabilityEngine:
    def test_match_winner(self) -> None:
        engine = ProbabilityEngine()
        dist = engine.compute_match_winner(50, 25, 25)
        assert abs(sum(dist.outcomes.values()) - 1.0) < 0.01
        assert all(v > 0 for v in dist.outcomes.values())

    def test_btts(self) -> None:
        engine = ProbabilityEngine()
        dist = engine.compute_btts(0.6, 0.4)
        assert abs(sum(dist.outcomes.values()) - 1.0) < 0.01
        assert "yes" in dist.outcomes
        assert "no" in dist.outcomes

    def test_over_under(self) -> None:
        engine = ProbabilityEngine()
        dist = engine.compute_over_under(0.55, 0.45)
        assert abs(sum(dist.outcomes.values()) - 1.0) < 0.01

    def test_double_chance(self) -> None:
        engine = ProbabilityEngine()
        dist = engine.compute_double_chance(0.5, 0.3, 0.2)
        assert abs(sum(dist.outcomes.values()) - 1.0) < 0.01
        assert len(dist.outcomes) == 3

    def test_normalize(self) -> None:
        engine = ProbabilityEngine()
        dist = engine.normalize({"a": 3, "b": 7})
        assert abs(sum(dist.outcomes.values()) - 1.0) < 0.01
        assert dist.outcomes["b"] > dist.outcomes["a"]

    def test_clip_probabilities(self) -> None:
        result = ProbabilityEngine.clip_probabilities({"a": 0.001, "b": 0.999})
        assert result.outcomes["a"] >= 0.01
        # After clipping and re-normalizing, b gets renormalized above 0.95
        assert result.outcomes["b"] > result.outcomes["a"]


# ===== Consensus Engine Tests =====


class TestConsensusEngine:
    def test_aggregate(self) -> None:
        from app.ai.models import (
            AnalysisResult,
            ConfidenceResult,
            FeatureVector,
            MatchOutcome,
            RuleResult,
        )

        engine = ConsensusEngine()
        features = FeatureVector(fixture_id=1, home_team_id=1, away_team_id=2)
        features.features["test"] = 1.0
        analysis = AnalysisResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            status=AnalysisStatus.SUCCESS,
            features=features,
            confidence=ConfidenceResult(
                overall=0.7,
                risk=0.3,
                stability=0.6,
                data_quality=0.8,
                provider_quality=0.7,
            ),
            rules=[
                RuleResult(
                    rule_id="r1",
                    name="R1",
                    weight=0.5,
                    impact=0.3,
                    outcome=MatchOutcome.HOME_WIN,
                    description="test",
                    explanation="test",
                )
            ],
        )
        result = engine.aggregate(analysis)
        assert result.source_count >= 2
        assert result.agreement_score >= 0.0


# ===== Risk Engine Tests =====


class TestRiskEngine:
    def test_assess(self) -> None:
        from app.ai.models import AnalysisResult, ConfidenceResult, FeatureVector

        engine = RiskEngine()
        features = FeatureVector(fixture_id=1, home_team_id=1, away_team_id=2)
        features.features["test"] = 1.0
        analysis = AnalysisResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            status=AnalysisStatus.SUCCESS,
            features=features,
            confidence=ConfidenceResult(
                overall=0.8,
                risk=0.2,
                stability=0.7,
                data_quality=0.9,
                provider_quality=0.8,
            ),
        )
        risk = engine.assess(analysis)
        assert risk.level in (
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.VERY_HIGH,
        )
        assert 0 <= risk.score <= 1

    def test_risk_level_mapping(self) -> None:
        engine = RiskEngine()
        assert engine._risk_level(0.1) == RiskLevel.LOW
        assert engine._risk_level(0.4) == RiskLevel.MEDIUM
        assert engine._risk_level(0.6) == RiskLevel.HIGH
        assert engine._risk_level(0.9) == RiskLevel.VERY_HIGH


# ===== Value Bet Engine Tests =====


class TestValueBetEngine:
    def test_find_value(self) -> None:
        engine = ValueBetEngine()
        dist = ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes={"home": 0.55, "draw": 0.25, "away": 0.20},
        )
        odds = {"home": 2.2, "draw": 3.5, "away": 3.8}
        bets = engine.find_value(dist, odds)
        assert isinstance(bets, list)

    def test_no_value_with_bad_odds(self) -> None:
        engine = ValueBetEngine()
        dist = ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes={"home": 0.4, "draw": 0.3, "away": 0.3},
        )
        odds = {"home": 1.1, "draw": 1.1, "away": 1.1}
        bets = engine.find_value(dist, odds)
        assert len(bets) == 0

    def test_kelly(self) -> None:
        engine = ValueBetEngine()
        kelly = engine._kelly(0.6, 2.0)
        assert kelly.fraction > 0
        assert kelly.recommended is True

    def test_kelly_no_edge(self) -> None:
        engine = ValueBetEngine()
        kelly = engine._kelly(0.4, 2.0)
        assert kelly.fraction == 0.0


# ===== Calibration Tests =====


class TestCalibrationEngine:
    def test_calibrate_no_offsets(self) -> None:
        engine = CalibrationEngine()
        dist = ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes={"home": 0.5, "draw": 0.3, "away": 0.2},
        )
        result = engine.calibrate(dist)
        assert result.outcomes == dist.outcomes

    def test_calibrate_with_offsets(self) -> None:
        engine = CalibrationEngine()
        engine.set_offsets("match_winner", {"home": 0.05, "away": -0.05})
        dist = ProbabilityDistribution(
            market=PredictionMarket.MATCH_WINNER,
            outcomes={"home": 0.5, "draw": 0.3, "away": 0.2},
        )
        result = engine.calibrate(dist)
        assert result.outcomes["home"] > dist.outcomes["home"]


# ===== Validator Tests =====


class TestPredictionValidator:
    def test_validate_success(self) -> None:
        from app.ai.models import AnalysisResult, FeatureVector

        validator = PredictionValidator()
        features = FeatureVector(fixture_id=1, home_team_id=1, away_team_id=2)
        features.features["a"] = 1.0
        features.features["b"] = 2.0
        features.features["c"] = 3.0
        analysis = AnalysisResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            status=AnalysisStatus.SUCCESS,
            features=features,
        )
        validator.validate(analysis)  # Should not raise

    def test_validate_insufficient_features(self) -> None:
        from app.ai.models import AnalysisResult, FeatureVector

        validator = PredictionValidator()
        features = FeatureVector(fixture_id=1, home_team_id=1, away_team_id=2)
        features.features["a"] = 1.0
        analysis = AnalysisResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            status=AnalysisStatus.SUCCESS,
            features=features,
        )
        with pytest.raises(InsufficientAnalysisError):
            validator.validate(analysis)

    def test_validate_failed_analysis(self) -> None:
        from app.ai.models import AnalysisResult

        validator = PredictionValidator()
        analysis = AnalysisResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            status=AnalysisStatus.FAILED,
        )
        with pytest.raises(InsufficientAnalysisError):
            validator.validate(analysis)

    def test_validate_low_confidence(self) -> None:
        from app.ai.models import AnalysisResult, ConfidenceResult, FeatureVector

        validator = PredictionValidator()
        features = FeatureVector(fixture_id=1, home_team_id=1, away_team_id=2)
        features.features["a"] = 1.0
        features.features["b"] = 2.0
        features.features["c"] = 3.0
        analysis = AnalysisResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            status=AnalysisStatus.SUCCESS,
            features=features,
            confidence=ConfidenceResult(
                overall=0.05,
                risk=0.9,
                stability=0.1,
                data_quality=0.1,
                provider_quality=0.1,
            ),
        )
        with pytest.raises(LowConfidenceError):
            validator.validate(analysis)


# ===== History Tests =====


class TestPredictionHistory:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self) -> None:
        store = PredictionHistoryStore()
        result = PredictionResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
        )
        record = await store.store(result)
        assert record.id is not None
        assert record.fixture_id == 1

        latest = await store.get_latest(1)
        assert latest is not None
        assert latest.id == record.id

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        store = PredictionHistoryStore()
        for _ in range(3):
            await store.store(
                PredictionResult(fixture_id=1, home_team_id=1, away_team_id=2)
            )
        records = await store.get_all(1)
        assert len(records) == 3

    @pytest.mark.asyncio
    async def test_record_outcome(self) -> None:
        store = PredictionHistoryStore()
        await store.store(
            PredictionResult(fixture_id=1, home_team_id=1, away_team_id=2)
        )
        await store.record_outcome(1, "home")
        latest = await store.get_latest(1)
        assert latest is not None
        assert latest.actual_outcome == "home"

    @pytest.mark.asyncio
    async def test_accuracy(self) -> None:
        store = PredictionHistoryStore()
        await store.record_outcome(1, "home")
        accuracy = await store.get_accuracy()
        assert 0 <= accuracy <= 1


# ===== Registry Tests =====


class TestPredictorRegistry:
    def test_register_and_get(self) -> None:
        from app.prediction.predictors.winner import WinnerPredictor

        reg = PredictorRegistry()
        reg.register(WinnerPredictor())
        assert PredictionMarket.MATCH_WINNER in reg
        assert len(reg) == 1

    def test_get_all(self) -> None:
        from app.prediction.predictors.btts import BTTSPredictor
        from app.prediction.predictors.winner import WinnerPredictor

        reg = PredictorRegistry()
        reg.register(WinnerPredictor())
        reg.register(BTTSPredictor())
        assert len(reg.get_all()) == 2


# ===== Predictor Tests =====


class TestWinnerPredictor:
    @pytest.mark.asyncio
    async def test_predict(self) -> None:
        from app.prediction.predictors.winner import WinnerPredictor

        predictor = WinnerPredictor()
        features = {
            "home_form_points": 12,
            "away_form_points": 6,
            "home_goal_diff_per_game": 1.0,
            "away_goal_diff_per_game": 0.2,
            "standings_advantage": 0.25,
            "venue_advantage": 0.3,
            "h2h_advantage": 0.2,
            "home_momentum": 0.7,
            "away_momentum": 0.4,
        }
        result = await predictor.predict(features)
        assert result.market == PredictionMarket.MATCH_WINNER
        assert abs(sum(result.distribution.outcomes.values()) - 1.0) < 0.01
        assert result.explanation is not None


class TestBTTSPredictor:
    @pytest.mark.asyncio
    async def test_predict(self) -> None:
        from app.prediction.predictors.btts import BTTSPredictor

        predictor = BTTSPredictor()
        features: dict[str, object] = {
            "home_avg_scored": 1.5,
            "away_avg_scored": 1.2,
            "home_avg_conceded": 0.8,
            "away_avg_conceded": 1.0,
            "total_expected_goals": 2.7,
        }
        result = await predictor.predict(features)
        assert result.market == PredictionMarket.BTTS
        assert abs(sum(result.distribution.outcomes.values()) - 1.0) < 0.01


class TestOverUnderPredictor:
    @pytest.mark.asyncio
    async def test_predict(self) -> None:
        from app.prediction.predictors.over_under import OverUnderPredictor

        predictor = OverUnderPredictor()
        features: dict[str, object] = {
            "total_expected_goals": 3.0,
            "home_avg_scored": 1.8,
            "away_avg_scored": 1.2,
            "home_avg_conceded": 0.9,
            "away_avg_conceded": 1.1,
        }
        result = await predictor.predict(features)
        assert result.market == PredictionMarket.OVER_UNDER_25
        assert abs(sum(result.distribution.outcomes.values()) - 1.0) < 0.01


# ===== Property-Based Tests =====


class TestPropertyBased:
    def test_winner_probabilities_sum_to_one(self) -> None:
        engine = ProbabilityEngine()
        for h in [0, 20, 40, 60, 80, 100]:
            for d in [0, 10, 25, 40]:
                for a in [0, 20, 40, 60, 80, 100]:
                    dist = engine.compute_match_winner(h, d, a)
                    assert abs(sum(dist.outcomes.values()) - 1.0) < 0.01

    def test_probabilities_never_negative(self) -> None:
        engine = ProbabilityEngine()
        dist = engine.compute_match_winner(0, 0, 0)
        for v in dist.outcomes.values():
            assert v >= 0

    async def test_confidence_in_range(self) -> None:
        from app.prediction.predictors.winner import WinnerPredictor

        predictor = WinnerPredictor()
        for home_form in range(0, 16):
            for away_form in range(0, 16):
                features: dict[str, object] = {
                    "home_form_points": home_form,
                    "away_form_points": away_form,
                    "home_goal_diff_per_game": 0,
                    "away_goal_diff_per_game": 0,
                    "standings_advantage": 0,
                    "venue_advantage": 0,
                    "h2h_advantage": 0,
                    "home_momentum": 0,
                    "away_momentum": 0,
                }
                result = await predictor.predict(features)
                assert 0 <= result.confidence <= 1


# ===== Full Integration Test =====


class TestPredictionEngineIntegration:
    @pytest.mark.asyncio
    async def test_full_prediction_cycle(self) -> None:
        engine = _make_prediction_engine()
        req = PredictionRequest(
            fixture_id=1000,
            home_team_id=1,
            away_team_id=2,
            competition_id=10,
            force_refresh=True,
        )
        result = await engine.predict(req)
        assert result.fixture_id == 1000
        assert len(result.predictions) > 0
        assert result.prediction_time_ms > 0
        assert result.overall_confidence >= 0

    @pytest.mark.asyncio
    async def test_prediction_caching(self) -> None:
        engine = _make_prediction_engine()
        req = PredictionRequest(
            fixture_id=2000,
            home_team_id=1,
            away_team_id=2,
            force_refresh=True,
        )
        result1 = await engine.predict(req)
        result2 = await engine.predict(req)
        assert result2.fixture_id == result1.fixture_id

    @pytest.mark.asyncio
    async def test_summary(self) -> None:
        engine = _make_prediction_engine()
        req = PredictionRequest(
            fixture_id=3000,
            home_team_id=1,
            away_team_id=2,
            force_refresh=True,
        )
        summary = await engine.get_summary(req)
        assert summary.fixture_id == 3000
        assert summary.confidence >= 0
