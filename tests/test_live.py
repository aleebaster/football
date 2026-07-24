"""Tests for Live Engine — comprehensive tests for all components."""

import pytest

from app.live.dispatcher import EventDispatcher
from app.live.events import EventFactory, LiveEvent
from app.live.exceptions import (
    LiveEngineError,
    QueueError,
    RecoveryError,
    WorkerError,
)
from app.live.heartbeat import HeartbeatMonitor
from app.live.metrics import LiveMetricsCollector
from app.live.models import (
    HeartbeatInfo,
    LiveMatch,
    LiveMetrics,
    MatchState,
    WorkerInfo,
    WorkerStatus,
)
from app.live.publisher import EventPublisher
from app.live.queue import MatchQueue
from app.live.state import StateRegistry

# ===== Model Tests =====


class TestLiveMatch:
    def test_live_match_defaults(self) -> None:
        m = LiveMatch(fixture_id=1)
        assert m.fixture_id == 1
        assert m.state == MatchState.SCHEDULED
        assert m.home_score is None

    def test_live_match_with_data(self) -> None:
        m = LiveMatch(
            fixture_id=100,
            home_team="Arsenal",
            away_team="Chelsea",
            state=MatchState.LIVE,
            home_score=2,
            away_score=1,
        )
        assert m.home_team == "Arsenal"
        assert m.state == MatchState.LIVE
        assert m.home_score == 2


class TestMatchState:
    def test_all_states_exist(self) -> None:
        assert MatchState.SCHEDULED.value == "scheduled"
        assert MatchState.LIVE.value == "live"
        assert MatchState.FINISHED.value == "finished"
        assert MatchState.HALF_TIME.value == "half_time"


class TestWorkerInfo:
    def test_worker_info_defaults(self) -> None:
        w = WorkerInfo(worker_id="w1")
        assert w.worker_id == "w1"
        assert w.status == WorkerStatus.IDLE
        assert w.processed_count == 0


class TestLiveMetrics:
    def test_metrics_defaults(self) -> None:
        m = LiveMetrics()
        assert m.active_matches == 0
        assert m.workers_total == 0
        assert m.events_published == 0


# ===== Event Tests =====


class TestEventFactory:
    def test_match_started_event(self) -> None:
        match = LiveMatch(fixture_id=1, home_team="A", away_team="B")
        event = EventFactory.match_started(match)
        assert event.event_type == "match_started"
        assert event.fixture_id == 1
        assert event.data["home_team"] == "A"

    def test_prediction_updated_event(self) -> None:
        event = EventFactory.prediction_updated(fixture_id=100, confidence=0.85)
        assert event.event_type == "prediction_updated"
        assert event.fixture_id == 100
        assert event.data["confidence"] == 0.85

    def test_signal_created_event(self) -> None:
        event = EventFactory.signal_created(
            fixture_id=100, signal_id="sig_1", market="match_winner", outcome="home"
        )
        assert event.event_type == "signal_created"
        assert event.data["signal_id"] == "sig_1"
        assert event.data["market"] == "match_winner"

    def test_goal_event(self) -> None:
        event = EventFactory.goal(
            fixture_id=100,
            team="Arsenal",
            player="Saka",
            minute=65,
            score_home=1,
            score_away=0,
        )
        assert event.event_type == "goal"
        assert event.data["player"] == "Saka"
        assert event.data["minute"] == 65

    def test_odds_changed_event(self) -> None:
        event = EventFactory.odds_changed(fixture_id=100, market="over_under_25")
        assert event.event_type == "odds_changed"

    def test_match_finished_event(self) -> None:
        match = LiveMatch(fixture_id=1, home_score=2, away_score=1)
        event = EventFactory.match_finished(match)
        assert event.event_type == "match_finished"
        assert event.data["home_score"] == 2

    def test_heartbeat_event(self) -> None:
        event = EventFactory.heartbeat(active_matches=5, workers=3)
        assert event.event_type == "heartbeat"
        assert event.data["active_matches"] == 5

    def test_event_correlation_id(self) -> None:
        event = EventFactory.prediction_updated(fixture_id=1, correlation_id="corr_abc")
        assert event.correlation_id == "corr_abc"

    def test_event_has_unique_id(self) -> None:
        e1 = EventFactory.heartbeat()
        e2 = EventFactory.heartbeat()
        assert e1.event_id != e2.event_id


# ===== Queue Tests =====


class TestMatchQueue:
    def test_empty_queue(self) -> None:
        q = MatchQueue()
        assert q.is_empty
        assert q.size == 0

    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self) -> None:
        q = MatchQueue()
        match = LiveMatch(fixture_id=1)
        await q.enqueue(match)
        assert q.size == 1
        result = await q.dequeue()
        assert result is not None
        assert result.fixture_id == 1
        assert q.is_empty

    @pytest.mark.asyncio
    async def test_priority_takes_precedence(self) -> None:
        q = MatchQueue()
        normal = LiveMatch(fixture_id=1)
        priority = LiveMatch(fixture_id=2)
        await q.enqueue(normal)
        await q.enqueue_priority(priority)
        result = await q.dequeue()
        assert result is not None
        assert result.fixture_id == 2

    @pytest.mark.asyncio
    async def test_mark_processed_prevents_reenqueue(self) -> None:
        q = MatchQueue()
        match = LiveMatch(fixture_id=1)
        await q.enqueue(match)
        await q.mark_processed(1)
        await q.enqueue(match)  # Should be skipped
        assert q.size == 1  # Only the first one

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        q = MatchQueue()
        await q.enqueue(LiveMatch(fixture_id=1))
        await q.enqueue(LiveMatch(fixture_id=2))
        await q.clear()
        assert q.is_empty

    @pytest.mark.asyncio
    async def test_peek(self) -> None:
        q = MatchQueue()
        match = LiveMatch(fixture_id=42)
        await q.enqueue(match)
        result = await q.peek()
        assert result is not None
        assert result.fixture_id == 42
        assert q.size == 1  # peek doesn't remove

    def test_stats(self) -> None:
        q = MatchQueue()
        stats = q.get_stats()
        assert stats["total"] == 0
        assert stats["priority"] == 0


# ===== State Registry Tests =====


class TestStateRegistry:
    @pytest.mark.asyncio
    async def test_update_and_get_match_state(self) -> None:
        reg = StateRegistry()
        await reg.update_match_state(1, MatchState.LIVE)
        state = await reg.get_match_state(1)
        assert state == MatchState.LIVE

    @pytest.mark.asyncio
    async def test_store_and_get_match_data(self) -> None:
        reg = StateRegistry()
        match = LiveMatch(fixture_id=1, home_team="A")
        await reg.store_match(match)
        data = await reg.get_match_data(1)
        assert data is not None
        assert data.home_team == "A"

    @pytest.mark.asyncio
    async def test_get_active_matches(self) -> None:
        reg = StateRegistry()
        await reg.update_match_state(1, MatchState.LIVE)
        await reg.update_match_state(2, MatchState.FINISHED)
        active = await reg.get_active_matches()
        assert 1 in active
        assert 2 not in active

    @pytest.mark.asyncio
    async def test_worker_registration(self) -> None:
        reg = StateRegistry()
        await reg.register_worker("w1")
        worker = await reg.get_worker("w1")
        assert worker is not None
        assert worker.worker_id == "w1"

    @pytest.mark.asyncio
    async def test_worker_status_update(self) -> None:
        reg = StateRegistry()
        await reg.register_worker("w1")
        await reg.update_worker_status("w1", WorkerStatus.PROCESSING, fixture_id=100)
        worker = await reg.get_worker("w1")
        assert worker is not None
        assert worker.status == WorkerStatus.PROCESSING
        assert worker.current_fixture_id == 100

    def test_heartbeat(self) -> None:
        reg = StateRegistry()
        reg.record_heartbeat()
        hb = reg.get_heartbeat()
        assert hb.timestamp is not None

    def test_uptime(self) -> None:
        reg = StateRegistry()
        uptime = reg.get_uptime()
        assert uptime >= 0

    def test_metrics_snapshot(self) -> None:
        reg = StateRegistry()
        snap = reg.get_metrics_snapshot()
        assert "active_matches" in snap
        assert "uptime_seconds" in snap


# ===== Publisher Tests =====


class TestEventPublisher:
    @pytest.mark.asyncio
    async def test_publish_to_handler(self) -> None:
        publisher = EventPublisher()
        received: list[LiveEvent] = []

        async def handler(event: LiveEvent) -> None:
            received.append(event)

        publisher.register(handler)
        event = EventFactory.heartbeat()
        await publisher.publish(event)
        assert len(received) == 1
        assert received[0].event_type == "heartbeat"

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self) -> None:
        publisher = EventPublisher()
        received: list[LiveEvent] = []

        async def handler(event: LiveEvent) -> None:
            received.append(event)

        publisher.register(handler)
        events: list[LiveEvent] = [EventFactory.heartbeat() for _ in range(5)]
        await publisher.publish_many(events)
        assert len(received) == 5

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_break_others(self) -> None:
        publisher = EventPublisher()
        received: list[LiveEvent] = []

        async def bad_handler(event: LiveEvent) -> None:
            raise ValueError("oops")

        async def good_handler(event: LiveEvent) -> None:
            received.append(event)

        publisher.register(bad_handler)
        publisher.register(good_handler)
        await publisher.publish(EventFactory.heartbeat())
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_recent_events_buffer(self) -> None:
        publisher = EventPublisher()
        for _ in range(10):
            await publisher.publish(EventFactory.heartbeat())
        recent = publisher.get_recent_events(5)
        assert len(recent) == 5

    def test_unregister(self) -> None:
        publisher = EventPublisher()

        async def handler(event: LiveEvent) -> None:
            pass

        publisher.register(handler)
        assert publisher.handler_count == 1
        publisher.unregister(handler)
        assert publisher.handler_count == 0

    def test_published_count(self) -> None:
        publisher = EventPublisher()
        assert publisher.published_count == 0


# ===== Dispatcher Tests =====


class TestEventDispatcher:
    @pytest.mark.asyncio
    async def test_dispatch(self) -> None:
        publisher = EventPublisher()
        dispatcher = EventDispatcher(publisher)
        received: list[LiveEvent] = []

        async def handler(event: LiveEvent) -> None:
            received.append(event)

        publisher.register(handler)
        event = EventFactory.heartbeat()
        await dispatcher.dispatch(event)
        assert len(received) == 1


# ===== Heartbeat Tests =====


class TestHeartbeatMonitor:
    def test_heartbeat_info(self) -> None:
        reg = StateRegistry()
        monitor = HeartbeatMonitor(state_registry=reg)
        info = monitor.get_info()
        assert isinstance(info, HeartbeatInfo)


# ===== Metrics Tests =====


class TestLiveMetricsCollector:
    def test_metrics_defaults(self) -> None:
        reg = StateRegistry()
        collector = LiveMetricsCollector(reg)
        metrics = collector.get_metrics()
        assert isinstance(metrics, LiveMetrics)
        assert metrics.active_matches == 0

    def test_record_times(self) -> None:
        reg = StateRegistry()
        collector = LiveMetricsCollector(reg)
        collector.record_prediction_time(100.0)
        collector.record_signal_time(50.0)
        collector.record_provider_latency(30.0)
        metrics = collector.get_metrics()
        assert metrics.avg_prediction_time_ms == 100.0
        assert metrics.avg_signal_time_ms == 50.0
        assert metrics.provider_latency_ms == 30.0


# ===== Exception Tests =====


class TestExceptions:
    def test_live_engine_error(self) -> None:
        e = LiveEngineError("test", details={"key": "value"})
        assert str(e) == "test"
        assert e.details["key"] == "value"

    def test_worker_error(self) -> None:
        e = WorkerError("worker failed")
        assert isinstance(e, LiveEngineError)

    def test_queue_error(self) -> None:
        e = QueueError("queue full")
        assert isinstance(e, LiveEngineError)

    def test_recovery_error(self) -> None:
        e = RecoveryError("recovery failed")
        assert isinstance(e, LiveEngineError)


# ===== Mapper Tests =====


class TestLiveMapper:
    def test_to_live_match_dto(self) -> None:
        from app.application.mapper import Mapper

        match = LiveMatch(
            fixture_id=1, home_team="A", away_team="B", state=MatchState.LIVE
        )
        dto = Mapper.to_live_match_dto(match)
        assert dto.fixture_id == 1
        assert dto.home_team == "A"
        assert dto.state == "live"

    def test_to_live_match_dto_none(self) -> None:
        from app.application.mapper import Mapper

        dto = Mapper.to_live_match_dto(None)
        assert dto.fixture_id == 0

    def test_to_live_event_dto(self) -> None:
        from app.application.mapper import Mapper

        event = EventFactory.heartbeat()
        dto = Mapper.to_live_event_dto(event)
        assert dto.event_type == "heartbeat"

    def test_to_live_event_dto_none(self) -> None:
        from app.application.mapper import Mapper

        dto = Mapper.to_live_event_dto(None)
        assert dto.event_type == ""

    def test_to_worker_dto(self) -> None:
        from app.application.mapper import Mapper

        worker = WorkerInfo(worker_id="w1", status=WorkerStatus.IDLE)
        dto = Mapper.to_worker_dto(worker)
        assert dto.worker_id == "w1"
        assert dto.status == "idle"

    def test_to_heartbeat_dto(self) -> None:
        from app.application.mapper import Mapper

        hb = HeartbeatInfo(workers_healthy=3, workers_total=5)
        dto = Mapper.to_heartbeat_dto(hb)
        assert dto.workers_healthy == 3
        assert dto.workers_total == 5

    def test_to_live_metrics_dto(self) -> None:
        from app.application.mapper import Mapper

        metrics = LiveMetrics(active_matches=5, events_published=100)
        dto = Mapper.to_live_metrics_dto(metrics)
        assert dto.active_matches == 5
        assert dto.events_published == 100

    def test_to_live_status_dto(self) -> None:
        from app.application.mapper import Mapper

        status: dict[str, object] = {
            "running": True,
            "active_matches": 3,
            "workers_active": 2,
        }
        dto = Mapper.to_live_status_dto(status)
        assert dto.running is True
        assert dto.active_matches == 3
