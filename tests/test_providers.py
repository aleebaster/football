"""Tests for Data Provider Platform."""

import pytest

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.providers.adapters.mock_provider import MockProvider
from app.providers.base import ProviderHealth
from app.providers.cache import CACHE_TTL, ProviderCache
from app.providers.exceptions import (
    AllProvidersFailedError,
    ProviderNotFoundError,
)
from app.providers.health import HealthChecker
from app.providers.http_client import HttpClientConfig
from app.providers.manager import ProviderManager
from app.providers.models import (
    Competition,
    Fixture,
    Odds,
    ProviderStatus,
    Standing,
    Team,
)
from app.providers.rate_limit import RateLimiter
from app.providers.registry import ProviderRegistry
from app.providers.retry import CircuitBreaker
from app.providers.scheduler import ProviderScheduler


def _make_provider_cache() -> ProviderCache:
    """Create a real ProviderCache backed by MemoryCache."""
    backend = MemoryCache(max_size=1000, default_ttl=300)
    cache_manager = CacheManager(backend)
    return ProviderCache(cache_manager)


def _make_fast_mock(name: str = "mock_fast", priority: int = 10) -> MockProvider:
    """Create a MockProvider with a custom name and priority."""
    p = MockProvider(priority=priority)
    p._name = name
    return p


def _make_slow_mock(name: str = "mock_slow", priority: int = 100) -> MockProvider:
    """Create a MockProvider with a custom name and priority."""
    p = MockProvider(priority=priority)
    p._name = name
    return p


class TrackableProvider(MockProvider):
    """MockProvider that tracks start/stop calls."""

    def __init__(self, name: str = "trackable", priority: int = 10) -> None:
        super().__init__(priority=priority)
        self._name = name
        self.start_called = False
        self.stop_called = False

    async def start(self) -> None:
        self.start_called = True

    async def stop(self) -> None:
        self.stop_called = True


class FailingStartProvider(MockProvider):
    """MockProvider that fails on start() but tracks stop()."""

    def __init__(self, name: str = "failing", priority: int = 20) -> None:
        super().__init__(priority=priority)
        self._name = name
        self.stop_called = False

    async def start(self) -> None:
        raise RuntimeError("Provider failed to start")

    async def stop(self) -> None:
        self.stop_called = True


# ===== ProviderHealth Tests =====


class TestProviderHealth:
    def test_initial_state(self) -> None:
        h = ProviderHealth()
        assert h.total_requests == 0
        assert h.success_rate == 100.0
        assert h.status == ProviderStatus.UNKNOWN

    def test_record_success(self) -> None:
        h = ProviderHealth()
        h.record_success(0.5)
        assert h.total_requests == 1
        assert h.successful_requests == 1
        assert h.average_response_time == 0.5
        assert h.status == ProviderStatus.HEALTHY

    def test_record_failure(self) -> None:
        h = ProviderHealth()
        h.record_failure()
        assert h.failed_requests == 1
        assert h.consecutive_failures == 1
        assert h.status == ProviderStatus.UNHEALTHY

    def test_consecutive_failures(self) -> None:
        h = ProviderHealth()
        for _ in range(5):
            h.record_failure()
        assert h.consecutive_failures == 5
        assert h.status == ProviderStatus.UNHEALTHY

    def test_success_resets_failures(self) -> None:
        h = ProviderHealth()
        h.record_failure()
        h.record_failure()
        h.record_success(0.1)
        assert h.consecutive_failures == 0

    def test_to_dict(self) -> None:
        h = ProviderHealth()
        d = h.to_dict()
        assert "status" in d
        assert "success_rate" in d


# ===== CircuitBreaker Tests =====


class TestCircuitBreaker:
    def test_closed_by_default(self) -> None:
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.allow_request() is True

    def test_opens_after_failures(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "open"
        assert cb.allow_request() is False

    def test_success_resets(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == "closed"
        assert cb.allow_request() is True


# ===== RateLimiter Tests =====


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire(self) -> None:
        rl = RateLimiter(rate=10.0, burst=5)
        await rl.acquire()
        status = rl.get_status()
        assert status["tokens"] < 5


# ===== HttpClient Tests =====


class TestHttpClientConfig:
    def test_defaults(self) -> None:
        config = HttpClientConfig()
        assert config.timeout == 30.0
        assert config.max_retries == 3


# ===== ProviderRegistry Tests =====


class TestProviderRegistry:
    def test_register_and_get(self) -> None:
        reg = ProviderRegistry()
        mock = MockProvider()
        reg.register(mock)
        assert reg.get("mock") is mock
        assert "mock" in reg
        assert len(reg) == 1

    def test_get_all_sorted_by_priority(self) -> None:
        reg = ProviderRegistry()
        p1 = _make_fast_mock("mock_fast", priority=10)
        p2 = _make_slow_mock("mock_slow", priority=100)
        reg.register(p1)
        reg.register(p2)
        providers = reg.get_all()
        assert len(providers) == 2
        assert providers[0].name == "mock_fast"
        assert providers[1].name == "mock_slow"

    def test_get_not_found(self) -> None:
        reg = ProviderRegistry()
        with pytest.raises(ProviderNotFoundError):
            reg.get("nonexistent")

    def test_unregister(self) -> None:
        reg = ProviderRegistry()
        reg.register(MockProvider())
        reg.unregister("mock")
        assert len(reg) == 0


# ===== MockProvider Tests =====


class TestMockProvider:
    @pytest.mark.asyncio
    async def test_check_health(self) -> None:
        mock = MockProvider()
        status = await mock.check_health()
        assert status == ProviderStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_competitions(self) -> None:
        mock = MockProvider()
        comps = await mock.competitions()
        assert len(comps) > 0
        assert isinstance(comps[0], Competition)

    @pytest.mark.asyncio
    async def test_teams(self) -> None:
        mock = MockProvider()
        teams = await mock.teams(1)
        assert len(teams) > 0
        assert isinstance(teams[0], Team)

    @pytest.mark.asyncio
    async def test_standings(self) -> None:
        mock = MockProvider()
        standings = await mock.standings(1)
        assert len(standings) > 0
        assert isinstance(standings[0], Standing)

    @pytest.mark.asyncio
    async def test_fixtures(self) -> None:
        mock = MockProvider()
        fixtures = await mock.fixtures(1)
        assert len(fixtures) > 0
        assert isinstance(fixtures[0], Fixture)

    @pytest.mark.asyncio
    async def test_fixture(self) -> None:
        mock = MockProvider()
        fixture = await mock.fixture(1000)
        assert fixture is not None
        assert isinstance(fixture, Fixture)

    @pytest.mark.asyncio
    async def test_live(self) -> None:
        mock = MockProvider()
        live = await mock.live()
        assert len(live) > 0

    @pytest.mark.asyncio
    async def test_events(self) -> None:
        mock = MockProvider()
        events = await mock.events(1000)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_statistics(self) -> None:
        mock = MockProvider()
        stats = await mock.statistics(1000)
        assert len(stats) > 0

    @pytest.mark.asyncio
    async def test_odds(self) -> None:
        mock = MockProvider()
        odds = await mock.odds(1000)
        assert odds is not None
        assert isinstance(odds, Odds)

    @pytest.mark.asyncio
    async def test_head_to_head(self) -> None:
        mock = MockProvider()
        h2h = await mock.head_to_head(101, 102)
        assert len(h2h) > 0

    @pytest.mark.asyncio
    async def test_search(self) -> None:
        mock = MockProvider()
        results = await mock.search("Premier")
        assert len(results) > 0


# ===== ProviderManager Tests =====


class TestProviderManager:
    @pytest.mark.asyncio
    async def test_competitions(self) -> None:
        reg = ProviderRegistry()
        reg.register(MockProvider())
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)
        comps = await mgr.competitions()
        assert len(comps) > 0

    def test_health_report(self) -> None:
        reg = ProviderRegistry()
        reg.register(MockProvider())
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)
        report = mgr.get_health_report()
        assert report["total"] == 1

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        reg = ProviderRegistry()
        reg.register(MockProvider())
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)
        await mgr.start()
        assert mgr._started is True
        await mgr.stop()
        assert mgr._started is False

    @pytest.mark.asyncio
    async def test_start_calls_provider_start(self) -> None:
        """ProviderManager.start() must call start() on each provider."""
        p1 = TrackableProvider("p1", priority=10)
        p2 = TrackableProvider("p2", priority=20)

        reg = ProviderRegistry()
        reg.register(p1)
        reg.register(p2)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        await mgr.start()
        assert p1.start_called is True
        assert p2.start_called is True

    @pytest.mark.asyncio
    async def test_stop_calls_provider_stop(self) -> None:
        """ProviderManager.stop() must call stop() on each provider."""
        p1 = TrackableProvider("p1", priority=10)
        p2 = TrackableProvider("p2", priority=20)

        reg = ProviderRegistry()
        reg.register(p1)
        reg.register(p2)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        await mgr.start()
        await mgr.stop()
        assert p1.stop_called is True
        assert p2.stop_called is True

    @pytest.mark.asyncio
    async def test_degraded_mode_on_start_failure(self) -> None:
        """If a provider fails to start, manager enters DEGRADED MODE."""
        good = TrackableProvider("good", priority=10)
        bad = FailingStartProvider("bad", priority=20)

        reg = ProviderRegistry()
        reg.register(good)
        reg.register(bad)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        await mgr.start()
        # Good provider should have been started despite bad failing
        assert good.start_called is True
        assert mgr.degraded is True
        assert "bad" in (mgr.degraded_reason or "")
        report = mgr.get_health_report()
        assert report["degraded"] is True
        assert report["degraded_reason"] is not None

        await mgr.stop()
        assert bad.stop_called is True

    @pytest.mark.asyncio
    async def test_degraded_mode_all_providers_fail(self) -> None:
        """If ALL providers fail to start, manager enters DEGRADED MODE."""
        bad1 = FailingStartProvider("bad1", priority=10)
        bad2 = FailingStartProvider("bad2", priority=20)

        reg = ProviderRegistry()
        reg.register(bad1)
        reg.register(bad2)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        await mgr.start()
        assert mgr.degraded is True
        assert mgr.degraded_reason is not None
        assert "bad1" in mgr.degraded_reason
        assert "bad2" in mgr.degraded_reason
        assert "Provider failed to start" in mgr.degraded_reason

        report = mgr.get_health_report()
        assert report["degraded"] is True
        assert report["degraded_reason"] is not None

        await mgr.stop()
        # After stop, degraded should be reset
        assert mgr.degraded is False
        assert mgr.degraded_reason is None


# ===== ProviderManager Fallback Tests =====


class TestProviderManagerFallback:
    """Integration tests for fallback, failover, priorities, and health switching."""

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self) -> None:
        """When the primary provider fails, fallback to the secondary."""
        primary = _make_fast_mock("primary", priority=10)
        secondary = _make_slow_mock("secondary", priority=20)

        # Make primary always fail by overriding competitions
        original = primary.competitions

        async def failing_competitions() -> list[Competition]:
            raise RuntimeError("Primary provider is down")

        primary.competitions = failing_competitions  # type: ignore[method-assign]

        reg = ProviderRegistry()
        reg.register(primary)
        reg.register(secondary)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        comps = await mgr.competitions()
        assert len(comps) > 0
        # Primary should have recorded a failure
        assert primary.health_info.failed_requests == 1
        # Secondary should have succeeded
        assert secondary.health_info.successful_requests == 1

        # Restore original
        primary.competitions = original  # type: ignore[method-assign]

    @pytest.mark.asyncio
    async def test_failover_all_providers_fail(self) -> None:
        """When all providers fail, raise AllProvidersFailedError."""
        p1 = _make_fast_mock("p1", priority=10)
        p2 = _make_slow_mock("p2", priority=20)

        async def fail1() -> list[Competition]:
            raise RuntimeError("Provider 1 down")

        async def fail2() -> list[Competition]:
            raise RuntimeError("Provider 2 down")

        p1.competitions = fail1  # type: ignore[method-assign]
        p2.competitions = fail2  # type: ignore[method-assign]

        reg = ProviderRegistry()
        reg.register(p1)
        reg.register(p2)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        with pytest.raises(AllProvidersFailedError):
            await mgr.competitions()

    @pytest.mark.asyncio
    async def test_priority_order(self) -> None:
        """Providers should be tried in priority order (lower number = higher priority)."""
        slow = _make_slow_mock("slow", priority=100)
        fast = _make_fast_mock("fast", priority=1)
        medium = _make_slow_mock("medium", priority=50)

        call_order: list[str] = []

        original_fast = fast.competitions
        original_medium = medium.competitions
        original_slow = slow.competitions

        async def track_fast() -> list[Competition]:
            call_order.append("fast")
            return await original_fast()

        async def track_medium() -> list[Competition]:
            call_order.append("medium")
            return await original_medium()

        async def track_slow() -> list[Competition]:
            call_order.append("slow")
            return await original_slow()

        fast.competitions = track_fast  # type: ignore[method-assign]
        medium.competitions = track_medium  # type: ignore[method-assign]
        slow.competitions = track_slow  # type: ignore[method-assign]

        reg = ProviderRegistry()
        reg.register(slow)
        reg.register(fast)
        reg.register(medium)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        await mgr.competitions()
        # First call should go to highest priority (lowest number)
        assert call_order[0] == "fast"

        fast.competitions = original_fast  # type: ignore[method-assign]
        medium.competitions = original_medium  # type: ignore[method-assign]
        slow.competitions = original_slow  # type: ignore[method-assign]

    @pytest.mark.asyncio
    async def test_unhealthy_provider_skipped(self) -> None:
        """Unhealthy providers should be skipped in favor of healthy ones."""
        healthy = _make_fast_mock("healthy", priority=10)
        unhealthy = _make_slow_mock("unhealthy", priority=5)

        # Simulate unhealthy status
        for _ in range(10):
            unhealthy.health_info.record_failure()

        reg = ProviderRegistry()
        reg.register(healthy)
        reg.register(unhealthy)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        comps = await mgr.competitions()
        assert len(comps) > 0
        # Healthy provider should have been used
        assert healthy.health_info.successful_requests == 1
        # Unhealthy should NOT have been used
        assert unhealthy.health_info.successful_requests == 0

    @pytest.mark.asyncio
    async def test_recovery_after_provider_back(self) -> None:
        """After a provider recovers, it should be usable again when healthy."""
        primary = _make_fast_mock("primary", priority=10)
        secondary = _make_slow_mock("secondary", priority=20)

        failing = True

        async def sometimes_failing() -> list[Competition]:
            if failing:
                raise RuntimeError("Primary is down")
            return await original_primary()

        original_primary = primary.competitions
        primary.competitions = sometimes_failing  # type: ignore[method-assign]

        reg = ProviderRegistry()
        reg.register(primary)
        reg.register(secondary)
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        # First call: primary fails, secondary used
        comps = await mgr.competitions()
        assert len(comps) > 0
        assert primary.health_info.failed_requests == 1
        assert secondary.health_info.successful_requests == 1

        # Bring primary back to healthy by recording many successes
        for _ in range(10):
            primary.health_info.record_success(0.1)

        # Now primary recovers
        failing = False
        comps = await mgr.competitions()
        assert len(comps) > 0
        # Primary should have been used again (it's healthy and higher priority)
        assert primary.health_info.successful_requests >= 10

        primary.competitions = original_primary  # type: ignore[method-assign]

    @pytest.mark.asyncio
    async def test_cache_consistency(self) -> None:
        """All methods should use the centralized caching strategy."""
        reg = ProviderRegistry()
        reg.register(MockProvider())
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        # standings() uses _execute_with_cache
        standings1 = await mgr.standings(1)
        standings2 = await mgr.standings(1)
        assert len(standings1) == len(standings2)

        # Check cache has entries
        keys = await cache._cache.keys("provider:*")
        assert len(keys) > 0

    @pytest.mark.asyncio
    async def test_manager_lifecycle(self) -> None:
        """Manager start/stop should manage provider lifecycle."""
        reg = ProviderRegistry()
        reg.register(MockProvider())
        cache = _make_provider_cache()
        mgr = ProviderManager(reg, cache)

        assert mgr._started is False
        await mgr.start()
        assert mgr._started is True
        # Starting again should be idempotent
        await mgr.start()
        assert mgr._started is True

        await mgr.stop()
        assert mgr._started is False
        # Stopping again should be idempotent
        await mgr.stop()
        assert mgr._started is False


# ===== ProviderScheduler Tests =====


class TestProviderScheduler:
    def test_add_and_remove_job(self) -> None:
        sched = ProviderScheduler()

        async def dummy() -> None:
            pass

        sched.add_job("test", dummy, interval=60.0)
        assert "test" in sched.jobs
        sched.remove_job("test")
        assert "test" not in sched.jobs

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        sched = ProviderScheduler()

        async def dummy() -> None:
            pass

        sched.add_job("test", dummy, interval=60.0)
        sched.start()
        assert sched.is_running is True
        sched.stop()
        assert sched.is_running is False


# ===== ProviderCache Tests =====


class TestProviderCache:
    def test_cache_ttl_config(self) -> None:
        assert CACHE_TTL["live"] == 30
        assert CACHE_TTL["standings"] == 3600
        assert CACHE_TTL["teams"] == 86400

    @pytest.mark.asyncio
    async def test_cache_get_set(self) -> None:
        cache = _make_provider_cache()
        await cache.set("mock", "fixtures", "key1", [{"id": 1}])
        result = await cache.get("mock", "fixtures", "key1")
        assert result == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_cache_invalidate(self) -> None:
        cache = _make_provider_cache()
        await cache.set("mock", "fixtures", "key1", [{"id": 1}])
        await cache.set("mock", "standings", "key2", [{"pos": 1}])
        invalidated = await cache.invalidate("mock", "fixtures")
        assert invalidated == 1
        # fixtures should be gone
        result = await cache.get("mock", "fixtures", "key1")
        assert result is None
        # standings should still be there
        result = await cache.get("mock", "standings", "key2")
        assert result is not None

    @pytest.mark.asyncio
    async def test_cache_clear(self) -> None:
        cache = _make_provider_cache()
        await cache.set("mock", "fixtures", "key1", [{"id": 1}])
        await cache.set("other", "fixtures", "key2", [{"id": 2}])
        await cache.clear()
        result1 = await cache.get("mock", "fixtures", "key1")
        result2 = await cache.get("other", "fixtures", "key2")
        assert result1 is None
        assert result2 is None


# ===== HealthChecker Tests =====


class TestHealthChecker:
    @pytest.mark.asyncio
    async def test_check_provider(self) -> None:
        mock = MockProvider()
        checker = HealthChecker([mock])
        status = await checker.check_provider(mock)
        assert status == ProviderStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_all(self) -> None:
        mock = MockProvider()
        checker = HealthChecker([mock])
        results = await checker.check_all()
        assert "mock" in results
