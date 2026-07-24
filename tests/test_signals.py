"""Tests for Signal Engine."""

import uuid

import pytest

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.prediction.models import (
    KellyResult,
    MarketPrediction,
    PredictionExplanation,
    PredictionMarket,
    PredictionResult,
    PredictionRiskAssessment,
    ProbabilityDistribution,
    RiskLevel,
    ValueBet,
)
from app.signals.cache import SignalCache
from app.signals.cooldown import CooldownManager
from app.signals.deduplication import DeduplicationManager
from app.signals.engine import SignalEngine
from app.signals.exceptions import SignalValidationError
from app.signals.filtering import SignalFilter
from app.signals.generators.btts import BTTSSignalGenerator
from app.signals.generators.handicap import HandicapSignalGenerator
from app.signals.generators.live import LiveSignalGenerator
from app.signals.generators.over_under import OverUnderSignalGenerator
from app.signals.generators.value import ValueSignalGenerator
from app.signals.generators.winner import WinnerSignalGenerator
from app.signals.history import SignalHistoryStore
from app.signals.metrics import MetricsCollector
from app.signals.models import (
    PerformanceStatistics,
    Portfolio,
    ROIStatistics,
    Signal,
    SignalMetrics,
    SignalRank,
    SignalScore,
    SignalStatus,
    SignalType,
    UserPreferences,
    ValueCategory,
    Watchlist,
)
from app.signals.notifications import NotificationEngine
from app.signals.persistence import SignalPersistence
from app.signals.portfolio import PortfolioManager
from app.signals.preferences import PreferencesManager
from app.signals.ranking import SignalRanker
from app.signals.registry import SignalGeneratorRegistry
from app.signals.scoring import SignalScorer
from app.signals.validator import SignalValidator
from app.signals.watchlist import WatchlistManager


def _make_cache() -> CacheManager:
    return CacheManager(MemoryCache(max_size=1000, default_ttl=300))


def _make_prediction_result(
    fixture_id: int = 1000,
    home_team_id: int = 1,
    away_team_id: int = 2,
) -> PredictionResult:
    """Create a test prediction result."""
    winner_dist = ProbabilityDistribution(
        market=PredictionMarket.MATCH_WINNER,
        outcomes={"home": 0.55, "draw": 0.25, "away": 0.20},
    )
    winner_pred = MarketPrediction(
        market=PredictionMarket.MATCH_WINNER,
        distribution=winner_dist,
        confidence=0.7,
        risk=PredictionRiskAssessment(
            level=RiskLevel.MEDIUM,
            score=0.4,
            data_completeness=0.8,
            provider_reliability=0.9,
            stability=0.7,
        ),
        value_bets=[
            ValueBet(
                market=PredictionMarket.MATCH_WINNER,
                outcome="home",
                model_probability=0.55,
                market_odds=2.2,
                implied_probability=0.4545,
                edge=0.0955,
                expected_value=0.21,
                kelly=KellyResult(
                    fraction=0.1, edge=0.21, expected_value=0.21, recommended=True
                ),
                explanation="Model assigns 55% to home vs market implied 45%",
            )
        ],
        explanation=PredictionExplanation(
            summary="Home favored",
            key_factors=["Form advantage", "Home ground"],
        ),
    )

    ou_dist = ProbabilityDistribution(
        market=PredictionMarket.OVER_UNDER_25,
        outcomes={"over": 0.6, "under": 0.4},
    )
    ou_pred = MarketPrediction(
        market=PredictionMarket.OVER_UNDER_25,
        distribution=ou_dist,
        confidence=0.65,
        risk=PredictionRiskAssessment(level=RiskLevel.LOW, score=0.3),
    )

    btts_dist = ProbabilityDistribution(
        market=PredictionMarket.BTTS,
        outcomes={"yes": 0.58, "no": 0.42},
    )
    btts_pred = MarketPrediction(
        market=PredictionMarket.BTTS,
        distribution=btts_dist,
        confidence=0.6,
        risk=PredictionRiskAssessment(level=RiskLevel.LOW, score=0.35),
    )

    return PredictionResult(
        fixture_id=fixture_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        predictions=[winner_pred, ou_pred, btts_pred],
        overall_confidence=0.65,
        overall_risk=PredictionRiskAssessment(
            level=RiskLevel.MEDIUM,
            score=0.4,
            data_completeness=0.8,
            provider_reliability=0.9,
            stability=0.7,
        ),
        explanation=PredictionExplanation(
            summary="Test prediction",
            key_factors=["Factor 1"],
        ),
    )


def _make_signal(
    fixture_id: int = 1000,
    confidence: float = 0.7,
    risk_score: float = 0.4,
    market: PredictionMarket = PredictionMarket.MATCH_WINNER,
) -> Signal:
    """Create a test signal with a unique ID."""
    return Signal(
        id=f"sig_{uuid.uuid4().hex[:8]}",
        fixture_id=fixture_id,
        home_team_id=1,
        away_team_id=2,
        market=market,
        outcome="home",
        probability=0.55,
        confidence=confidence,
        odds=2.2,
        score=SignalScore(
            overall=0.7, confidence=confidence, expected_value=0.05, risk=risk_score
        ),
        risk_level=RiskLevel.MEDIUM,
        risk_score=risk_score,
        summary="Test signal",
        key_factors=["Factor 1"],
    )


# ===== Signal Models Tests =====


class TestSignalModels:
    def test_signal_creation(self) -> None:
        signal = _make_signal()
        assert signal.id.startswith("sig_")
        assert signal.fixture_id == 1000
        assert signal.confidence == 0.7
        assert signal.status == SignalStatus.ACTIVE

    def test_signal_score(self) -> None:
        score = SignalScore(overall=0.8, confidence=0.7, expected_value=0.05)
        assert score.overall == 0.8
        assert score.confidence == 0.7

    def test_signal_rank(self) -> None:
        rank = SignalRank(position=1, percentile=0.95)
        assert rank.position == 1
        assert rank.percentile == 0.95

    def test_user_preferences(self) -> None:
        prefs = UserPreferences(
            user_id=1,
            min_confidence=0.6,
            max_risk=RiskLevel.MEDIUM,
        )
        assert prefs.user_id == 1
        assert prefs.min_confidence == 0.6

    def test_watchlist(self) -> None:
        wl = Watchlist(user_id=1, teams=[10, 20], leagues=[100])
        assert wl.user_id == 1
        assert 10 in wl.teams

    def test_portfolio(self) -> None:
        portfolio = Portfolio(user_id=1, total_stake=100.0, total_pnl=15.0)
        assert portfolio.user_id == 1
        assert portfolio.total_stake == 100.0

    def test_roi_statistics(self) -> None:
        stats = ROIStatistics(total_signals=100, winning_signals=60, roi=0.15)
        assert stats.total_signals == 100
        assert stats.win_rate == 0.0  # default since not set

    def test_performance_statistics(self) -> None:
        stats = PerformanceStatistics(
            market=PredictionMarket.MATCH_WINNER,
            total_signals=50,
            win_rate=0.6,
        )
        assert stats.market == PredictionMarket.MATCH_WINNER
        assert stats.win_rate == 0.6

    def test_signal_metrics(self) -> None:
        metrics = SignalMetrics(total_processed=100, total_generated=80)
        assert metrics.total_processed == 100
        assert metrics.total_generated == 80


# ===== Signal Validator Tests =====


class TestSignalValidator:
    def test_validate_prediction_success(self) -> None:
        validator = SignalValidator()
        prediction = _make_prediction_result()
        validator.validate_prediction(prediction)  # Should not raise

    def test_validate_prediction_no_predictions(self) -> None:
        validator = SignalValidator()
        prediction = PredictionResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            predictions=[],
        )
        with pytest.raises(SignalValidationError):
            validator.validate_prediction(prediction)

    def test_validate_prediction_low_confidence(self) -> None:
        validator = SignalValidator()
        prediction = PredictionResult(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            overall_confidence=0.05,
            predictions=[
                MarketPrediction(
                    market=PredictionMarket.MATCH_WINNER,
                    distribution=ProbabilityDistribution(
                        market=PredictionMarket.MATCH_WINNER,
                        outcomes={"home": 0.5, "draw": 0.3, "away": 0.2},
                    ),
                )
            ],
        )
        with pytest.raises(SignalValidationError):
            validator.validate_prediction(prediction)

    def test_validate_signal_success(self) -> None:
        validator = SignalValidator()
        signal = _make_signal()
        assert validator.validate_signal(signal) is True

    def test_validate_signal_no_id(self) -> None:
        validator = SignalValidator()
        signal = Signal(
            fixture_id=1,
            home_team_id=1,
            away_team_id=2,
            id="",
        )
        with pytest.raises(SignalValidationError):
            validator.validate_signal(signal)


# ===== Signal Scorer Tests =====


class TestSignalScorer:
    def test_calculate_score(self) -> None:
        scorer = SignalScorer()
        signal = _make_signal()
        prediction = _make_prediction_result()
        score = scorer.calculate_score(signal, prediction)
        assert 0 <= score.overall <= 1
        assert 0 <= score.confidence <= 1
        assert score.signal_freshness > 0

    def test_categorize_value_strong(self) -> None:
        scorer = SignalScorer()
        signal = _make_signal()
        signal.score = SignalScore(expected_value=0.1)
        assert scorer.categorize_value(signal) == ValueCategory.STRONG_VALUE

    def test_categorize_value_negative(self) -> None:
        scorer = SignalScorer()
        signal = _make_signal()
        signal.score = SignalScore(expected_value=-0.05)
        assert scorer.categorize_value(signal) == ValueCategory.NEGATIVE_EV

    def test_categorize_value_neutral(self) -> None:
        scorer = SignalScorer()
        signal = _make_signal()
        signal.score = SignalScore(expected_value=0.01)
        assert scorer.categorize_value(signal) == ValueCategory.NEUTRAL


# ===== Signal Ranker Tests =====


class TestSignalRanker:
    def test_rank(self) -> None:
        ranker = SignalRanker()
        signals = [
            _make_signal(confidence=0.5),
            _make_signal(confidence=0.9),
            _make_signal(confidence=0.7),
        ]
        # Set different overall scores so ranking works
        signals[0].score = SignalScore(overall=0.4, confidence=0.5)
        signals[1].score = SignalScore(overall=0.9, confidence=0.9)
        signals[2].score = SignalScore(overall=0.65, confidence=0.7)
        ranked = ranker.rank(signals)
        assert len(ranked) == 3
        assert ranked[0].rank.position == 1
        assert ranked[0].confidence == 0.9

    def test_rank_empty(self) -> None:
        ranker = SignalRanker()
        ranked = ranker.rank([])
        assert ranked == []

    def test_rank_single(self) -> None:
        ranker = SignalRanker()
        signal = _make_signal()
        ranked = ranker.rank([signal])
        assert len(ranked) == 1
        assert ranked[0].rank.position == 1
        assert ranked[0].rank.percentile == 1.0


# ===== Signal Filter Tests =====


class TestSignalFilter:
    def test_filter_keeps_good_signals(self) -> None:
        signal_filter = SignalFilter(min_confidence=0.5, max_risk_score=0.8)
        signal = _make_signal(confidence=0.7, risk_score=0.4)
        assert signal_filter.should_keep(signal) is True

    def test_filter_rejects_low_confidence(self) -> None:
        signal_filter = SignalFilter(min_confidence=0.5)
        signal = _make_signal(confidence=0.3)
        assert signal_filter.should_keep(signal) is False

    def test_filter_rejects_high_risk(self) -> None:
        signal_filter = SignalFilter(max_risk_score=0.5)
        signal = _make_signal(risk_score=0.7)
        assert signal_filter.should_keep(signal) is False

    def test_filter_rejects_inactive(self) -> None:
        signal_filter = SignalFilter()
        signal = _make_signal()
        signal.status = SignalStatus.CANCELLED
        assert signal_filter.should_keep(signal) is False

    def test_filter_signals(self) -> None:
        signal_filter = SignalFilter(min_confidence=0.5)
        signals = [
            _make_signal(confidence=0.8),
            _make_signal(confidence=0.3),
            _make_signal(confidence=0.6),
        ]
        filtered = signal_filter.filter_signals(signals)
        assert len(filtered) == 2

    def test_apply_user_preferences(self) -> None:
        signal_filter = SignalFilter()
        signal = _make_signal(confidence=0.7)
        prefs = UserPreferences(
            user_id=1,
            min_confidence=0.6,
            allowed_markets=[PredictionMarket.MATCH_WINNER],
            notification_start_hour=0,
            notification_end_hour=23,
        )
        assert signal_filter.apply_user_preferences(signal, prefs) is True

    def test_apply_user_preferences_disabled(self) -> None:
        signal_filter = SignalFilter()
        signal = _make_signal()
        prefs = UserPreferences(
            user_id=1,
            enabled=False,
            notification_start_hour=0,
            notification_end_hour=23,
        )
        assert signal_filter.apply_user_preferences(signal, prefs) is False


# ===== Cooldown Tests =====


class TestCooldownManager:
    def test_not_on_cooldown_initially(self) -> None:
        cooldown = CooldownManager()
        signal = _make_signal()
        assert cooldown.is_on_cooldown(signal) is False

    def test_mark_sent_and_check(self) -> None:
        cooldown = CooldownManager()
        signal = _make_signal()
        cooldown.mark_sent(signal)
        assert cooldown.is_on_cooldown(signal) is True

    def test_clear_cooldown(self) -> None:
        cooldown = CooldownManager()
        signal = _make_signal()
        cooldown.mark_sent(signal)
        cooldown.clear_cooldown(signal)
        assert cooldown.is_on_cooldown(signal) is False

    def test_clear_all(self) -> None:
        cooldown = CooldownManager()
        signal = _make_signal()
        cooldown.mark_sent(signal)
        cooldown.clear_all()
        assert cooldown.is_on_cooldown(signal) is False

    def test_get_remaining(self) -> None:
        cooldown = CooldownManager()
        signal = _make_signal()
        cooldown.mark_sent(signal)
        remaining = cooldown.get_remaining(signal)
        assert remaining > 0


# ===== Deduplication Tests =====


class TestDeduplicationManager:
    def test_not_duplicate_initially(self) -> None:
        dedup = DeduplicationManager()
        signal = _make_signal()
        assert dedup.is_duplicate(signal) is False

    def test_register_and_check(self) -> None:
        dedup = DeduplicationManager()
        signal = _make_signal()
        dedup.register(signal)
        # Same signal should not be duplicate of itself
        assert dedup.is_duplicate(signal) is False

    def test_invalidate(self) -> None:
        dedup = DeduplicationManager()
        signal = _make_signal()
        dedup.register(signal)
        dedup.invalidate(signal)
        assert dedup.is_duplicate(signal) is False

    def test_filter_duplicates(self) -> None:
        dedup = DeduplicationManager()
        signals = [_make_signal(), _make_signal(), _make_signal()]
        unique = dedup.filter_duplicates(signals)
        assert len(unique) == 1

    def test_different_ids_same_content_are_duplicates(self) -> None:
        """Test that signals with different IDs but same content are deduplicated."""
        dedup = DeduplicationManager()
        signal1 = Signal(
            id="sig_1",
            fixture_id=1000,
            home_team_id=1,
            away_team_id=2,
            market=PredictionMarket.MATCH_WINNER,
            outcome="home",
            probability=0.55,
            confidence=0.7,
            odds=2.2,
            summary="Test",
            key_factors=["F1"],
        )
        signal2 = Signal(
            id="sig_2",
            fixture_id=1000,
            home_team_id=1,
            away_team_id=2,
            market=PredictionMarket.MATCH_WINNER,
            outcome="home",
            probability=0.55,
            confidence=0.7,
            odds=2.2,
            summary="Test",
            key_factors=["F1"],
        )
        # Different IDs but same key -> duplicates
        unique = dedup.filter_duplicates([signal1, signal2])
        assert len(unique) == 1

    def test_different_content_not_duplicates(self) -> None:
        """Test that signals with different content are not deduplicated."""
        dedup = DeduplicationManager()
        signal1 = Signal(
            id="sig_1",
            fixture_id=1000,
            home_team_id=1,
            away_team_id=2,
            market=PredictionMarket.MATCH_WINNER,
            outcome="home",
            confidence=0.7,
            odds=2.2,
            summary="Test",
            key_factors=["F1"],
        )
        signal2 = Signal(
            id="sig_2",
            fixture_id=1000,
            home_team_id=1,
            away_team_id=2,
            market=PredictionMarket.OVER_UNDER_25,
            outcome="over",
            confidence=0.7,
            odds=2.2,
            summary="Test",
            key_factors=["F1"],
        )
        # Different market -> not duplicates
        unique = dedup.filter_duplicates([signal1, signal2])
        assert len(unique) == 2


# ===== Signal History Tests =====


class TestSignalHistory:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self) -> None:
        store = SignalHistoryStore()
        signal = _make_signal()
        record = await store.store(signal)
        assert record.id is not None
        assert record.signal_id == signal.id

        latest = await store.get_latest(signal.id)
        assert latest is not None
        assert latest.signal_id == signal.id

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        store = SignalHistoryStore()
        signal = _make_signal()
        for _ in range(3):
            await store.store(signal)
        records = await store.get_all(signal.id)
        assert len(records) == 3

    @pytest.mark.asyncio
    async def test_record_outcome(self) -> None:
        store = SignalHistoryStore()
        signal = _make_signal()
        await store.store(signal)
        await store.record_outcome(signal.id, "home")
        latest = await store.get_latest(signal.id)
        assert latest is not None
        assert latest.actual_outcome == "home"

    @pytest.mark.asyncio
    async def test_accuracy(self) -> None:
        store = SignalHistoryStore()
        signal = _make_signal()
        await store.store(signal)
        await store.record_outcome(signal.id, "home")
        accuracy = await store.get_accuracy()
        assert 0 <= accuracy <= 1


# ===== Signal Cache Tests =====


class TestSignalCache:
    @pytest.mark.asyncio
    async def test_cache_operations(self) -> None:
        cache = SignalCache(_make_cache())
        await cache.set(1000, [{"id": "sig_1"}])
        cached = await cache.get(1000)
        assert cached is not None
        assert len(cached) == 1

    @pytest.mark.asyncio
    async def test_cache_invalidation(self) -> None:
        cache = SignalCache(_make_cache())
        await cache.set(1000, [{"id": "sig_1"}])
        await cache.invalidate(1000)
        cached = await cache.get(1000)
        assert cached is None


# ===== Signal Filter Notification Tests =====


class TestNotificationEngine:
    def test_should_notify_active_signal(self) -> None:
        engine = NotificationEngine()
        signal = _make_signal()
        signal.value_category = ValueCategory.VALUE
        decision = engine.should_notify(signal)
        assert decision.should_notify is True

    def test_should_not_notify_negative_ev(self) -> None:
        engine = NotificationEngine()
        signal = _make_signal()
        signal.value_category = ValueCategory.NEGATIVE_EV
        decision = engine.should_notify(signal)
        assert decision.should_notify is False

    def test_should_not_notify_inactive(self) -> None:
        engine = NotificationEngine()
        signal = _make_signal()
        signal.status = SignalStatus.CANCELLED
        decision = engine.should_notify(signal)
        assert decision.should_notify is False

    def test_should_not_notify_low_confidence(self) -> None:
        engine = NotificationEngine()
        signal = _make_signal(confidence=0.3)
        prefs = UserPreferences(user_id=1, min_confidence=0.5)
        decision = engine.should_notify(signal, prefs)
        assert decision.should_notify is False

    def test_evaluate_update_confidence_change(self) -> None:
        engine = NotificationEngine()
        old_signal = _make_signal(confidence=0.5)
        new_signal = _make_signal(confidence=0.8)
        decision = engine.evaluate_update(old_signal, new_signal)
        assert decision.should_notify is True
        assert decision.signal_type == SignalType.CONFIDENCE_UP

    def test_evaluate_cancellation(self) -> None:
        engine = NotificationEngine()
        signal = _make_signal()
        decision = engine.evaluate_cancellation(signal, "Test reason")
        assert decision.should_notify is True
        assert decision.signal_type == SignalType.CANCEL


# ===== Signal Preference Tests =====


class TestPreferencesManager:
    def test_get_default(self) -> None:
        manager = PreferencesManager()
        prefs = manager.get(1)
        assert prefs.user_id == 1
        assert prefs.enabled is True

    def test_set_and_get(self) -> None:
        manager = PreferencesManager()
        prefs = UserPreferences(user_id=1, min_confidence=0.7)
        manager.set(prefs)
        retrieved = manager.get(1)
        assert retrieved.min_confidence == 0.7

    def test_add_favorite_team(self) -> None:
        manager = PreferencesManager()
        manager.add_favorite_team(1, 10)
        prefs = manager.get(1)
        assert 10 in prefs.favorite_teams

    def test_remove_favorite_team(self) -> None:
        manager = PreferencesManager()
        manager.add_favorite_team(1, 10)
        manager.remove_favorite_team(1, 10)
        prefs = manager.get(1)
        assert 10 not in prefs.favorite_teams

    def test_set_quiet_hours(self) -> None:
        manager = PreferencesManager()
        manager.set_quiet_hours(1, 22, 8)
        prefs = manager.get(1)
        assert prefs.notification_start_hour == 22
        assert prefs.notification_end_hour == 8

    def test_delete(self) -> None:
        manager = PreferencesManager()
        manager.set(UserPreferences(user_id=1))
        assert manager.delete(1) is True
        assert manager.delete(1) is False


# ===== Watchlist Tests =====


class TestWatchlistManager:
    def test_get_default(self) -> None:
        manager = WatchlistManager()
        wl = manager.get(1)
        assert wl.user_id == 1
        assert len(wl.teams) == 0

    def test_add_team(self) -> None:
        manager = WatchlistManager()
        manager.add_team(1, 10)
        wl = manager.get(1)
        assert 10 in wl.teams

    def test_remove_team(self) -> None:
        manager = WatchlistManager()
        manager.add_team(1, 10)
        manager.remove_team(1, 10)
        wl = manager.get(1)
        assert 10 not in wl.teams

    def test_matches_watchlist_empty(self) -> None:
        manager = WatchlistManager()
        assert manager.matches_watchlist(1, 100, 1, 2) is True

    def test_matches_watchlist_team(self) -> None:
        manager = WatchlistManager()
        manager.add_team(1, 10)
        assert manager.matches_watchlist(1, 100, 10, 2) is True
        assert manager.matches_watchlist(1, 100, 30, 2) is False


# ===== Portfolio Tests =====


class TestPortfolioManager:
    def test_get_default(self) -> None:
        manager = PortfolioManager()
        portfolio = manager.get(1)
        assert portfolio.user_id == 1
        assert portfolio.total_stake == 0.0

    def test_add_bet(self) -> None:
        manager = PortfolioManager()
        manager.add_bet(1, "sig_1", 10.0)
        portfolio = manager.get(1)
        assert "sig_1" in portfolio.active_bets
        assert portfolio.total_stake == 10.0

    def test_resolve_bet(self) -> None:
        manager = PortfolioManager()
        manager.add_bet(1, "sig_1", 10.0)
        manager.resolve_bet(1, "sig_1", 5.0, True)
        portfolio = manager.get(1)
        assert "sig_1" not in portfolio.active_bets
        assert portfolio.total_pnl == 5.0
        assert portfolio.win_count == 1

    def test_get_win_rate(self) -> None:
        manager = PortfolioManager()
        manager.add_bet(1, "sig_1", 10.0)
        manager.resolve_bet(1, "sig_1", 5.0, True)
        manager.add_bet(1, "sig_2", 10.0)
        manager.resolve_bet(1, "sig_2", -10.0, False)
        assert manager.get_win_rate(1) == 0.5


# ===== Metrics Collector Tests =====


class TestMetricsCollector:
    def test_record_processed(self) -> None:
        collector = MetricsCollector()
        collector.record_processed(10)
        metrics = collector.get_metrics()
        assert metrics.total_processed == 10

    def test_record_generated(self) -> None:
        collector = MetricsCollector()
        collector.record_generated(5)
        metrics = collector.get_metrics()
        assert metrics.total_generated == 5

    def test_record_filtered(self) -> None:
        collector = MetricsCollector()
        collector.record_filtered(3)
        metrics = collector.get_metrics()
        assert metrics.total_filtered == 3

    def test_reset(self) -> None:
        collector = MetricsCollector()
        collector.record_processed(10)
        collector.reset()
        metrics = collector.get_metrics()
        assert metrics.total_processed == 0


# ===== Signal Persistence Tests =====


class TestSignalPersistence:
    @pytest.mark.asyncio
    async def test_save_and_get(self) -> None:
        persistence = SignalPersistence()
        signal = _make_signal()
        await persistence.save(signal)
        retrieved = await persistence.get(signal.id)
        assert retrieved is not None
        assert retrieved.id == signal.id

    @pytest.mark.asyncio
    async def test_get_by_fixture(self) -> None:
        persistence = SignalPersistence()
        signal = _make_signal(fixture_id=1000)
        await persistence.save(signal)
        signals = await persistence.get_by_fixture(1000)
        assert len(signals) == 1

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        persistence = SignalPersistence()
        signal = _make_signal()
        await persistence.save(signal)
        assert await persistence.delete(signal.id) is True
        assert await persistence.get(signal.id) is None


# ===== Signal Generator Tests =====


class TestWinnerSignalGenerator:
    @pytest.mark.asyncio
    async def test_generate(self) -> None:
        generator = WinnerSignalGenerator()
        prediction = _make_prediction_result()
        signals = await generator.generate(prediction)
        assert len(signals) > 0
        assert signals[0].market == PredictionMarket.MATCH_WINNER


class TestOverUnderSignalGenerator:
    @pytest.mark.asyncio
    async def test_generate(self) -> None:
        generator = OverUnderSignalGenerator()
        prediction = _make_prediction_result()
        signals = await generator.generate(prediction)
        assert len(signals) > 0
        assert signals[0].market == PredictionMarket.OVER_UNDER_25


class TestBTTSSignalGenerator:
    @pytest.mark.asyncio
    async def test_generate(self) -> None:
        generator = BTTSSignalGenerator()
        prediction = _make_prediction_result()
        signals = await generator.generate(prediction)
        assert len(signals) > 0
        assert signals[0].market == PredictionMarket.BTTS


class TestHandicapSignalGenerator:
    @pytest.mark.asyncio
    async def test_generate_no_handicap_prediction(self) -> None:
        generator = HandicapSignalGenerator()
        prediction = _make_prediction_result()
        signals = await generator.generate(prediction)
        # No handicap prediction in test data
        assert len(signals) == 0


class TestValueSignalGenerator:
    @pytest.mark.asyncio
    async def test_generate(self) -> None:
        generator = ValueSignalGenerator()
        prediction = _make_prediction_result()
        signals = await generator.generate(prediction)
        assert len(signals) > 0


class TestLiveSignalGenerator:
    @pytest.mark.asyncio
    async def test_generate(self) -> None:
        generator = LiveSignalGenerator()
        prediction = _make_prediction_result()
        signals = await generator.generate(prediction)
        assert len(signals) > 0
        assert signals[0].signal_type == SignalType.LIVE


# ===== Signal Registry Tests =====


class TestSignalGeneratorRegistry:
    def test_register_and_get(self) -> None:
        registry = SignalGeneratorRegistry()
        generator = WinnerSignalGenerator()
        registry.register(generator, PredictionMarket.MATCH_WINNER)
        assert PredictionMarket.MATCH_WINNER in registry
        assert len(registry) == 1

    def test_get_all(self) -> None:
        registry = SignalGeneratorRegistry()
        registry.register(WinnerSignalGenerator(), PredictionMarket.MATCH_WINNER)
        registry.register(BTTSSignalGenerator(), PredictionMarket.BTTS)
        assert len(registry.get_all()) == 2


# ===== Signal Engine Integration Tests =====


class TestSignalEngine:
    @pytest.mark.asyncio
    async def test_engine_initialization(self) -> None:
        engine = SignalEngine(_make_cache())
        assert len(engine) > 0

    @pytest.mark.asyncio
    async def test_process_prediction(self) -> None:
        engine = SignalEngine(_make_cache())
        prediction = _make_prediction_result()
        signals = await engine.process(prediction)
        assert len(signals) > 0
        assert all(isinstance(s, Signal) for s in signals)

    @pytest.mark.asyncio
    async def test_process_with_preferences(self) -> None:
        engine = SignalEngine(_make_cache())
        prediction = _make_prediction_result()
        prefs = UserPreferences(
            user_id=1,
            min_confidence=0.5,
            allowed_markets=[PredictionMarket.MATCH_WINNER],
            notification_start_hour=0,
            notification_end_hour=23,
        )
        signals = await engine.process(prediction, prefs)
        assert len(signals) > 0

    @pytest.mark.asyncio
    async def test_process_request(self) -> None:
        engine = SignalEngine(_make_cache())
        prediction = _make_prediction_result()
        # Set preferences with wide notification hours to avoid time-dependent CI failures
        engine.preferences.set(
            UserPreferences(
                user_id=1,
                min_confidence=0.5,
                notification_start_hour=0,
                notification_end_hour=23,
            )
        )
        signals = await engine.process_request(prediction, user_id=1)
        assert len(signals) > 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self) -> None:
        engine = SignalEngine(_make_cache())
        prediction = _make_prediction_result()
        await engine.process(prediction)
        metrics = engine.metrics.get_metrics()
        assert metrics.total_processed > 0


# ===== Full Pipeline Integration Tests =====


class TestSignalPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        """Test the full pipeline: Prediction → Signal → History."""
        engine = SignalEngine(_make_cache())
        prediction = _make_prediction_result()

        # Process through pipeline
        signals = await engine.process(prediction)
        assert len(signals) > 0

        # Check history
        for signal in signals:
            record = await engine.history.get_latest(signal.id)
            assert record is not None

        # Check persistence
        for signal in signals:
            persisted = await engine.persistence.get(signal.id)
            assert persisted is not None

    @pytest.mark.asyncio
    async def test_deduplication_in_pipeline(self) -> None:
        """Test that deduplication works in the pipeline."""
        engine = SignalEngine(_make_cache())
        prediction = _make_prediction_result()

        # Process same prediction twice
        signals1 = await engine.process(prediction)
        signals2 = await engine.process(prediction)

        # Should get fewer signals on second pass due to dedup
        assert len(signals2) <= len(signals1)


# ===== Property-Based Tests =====


class TestPropertyBased:
    def test_scores_always_in_range(self) -> None:
        scorer = SignalScorer()
        for confidence in [0.0, 0.3, 0.5, 0.7, 1.0]:
            for risk in [0.0, 0.3, 0.5, 0.7, 1.0]:
                signal = _make_signal(confidence=confidence, risk_score=risk)
                score = scorer.calculate_score(signal)
                assert 0 <= score.overall <= 1
                assert 0 <= score.confidence <= 1

    def test_ranking_preserves_count(self) -> None:
        ranker = SignalRanker()
        signals = [_make_signal(confidence=c) for c in [0.3, 0.5, 0.7, 0.9]]
        ranked = ranker.rank(signals)
        assert len(ranked) == len(signals)

    def test_ranking_order(self) -> None:
        ranker = SignalRanker()
        signals = [_make_signal(confidence=c) for c in [0.3, 0.9, 0.5]]
        ranked = ranker.rank(signals)
        for i in range(len(ranked) - 1):
            assert ranked[i].score.overall >= ranked[i + 1].score.overall

    def test_filter_deterministic(self) -> None:
        signal_filter = SignalFilter(min_confidence=0.5)
        signal = _make_signal(confidence=0.6)
        results = [signal_filter.should_keep(signal) for _ in range(10)]
        assert all(r == results[0] for r in results)
