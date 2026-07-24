"""Comprehensive component tests for the Live Engine.

Tests cover:
- LiveScheduler: cycle execution, recovery integration
- LiveWorker: full pipeline processing, recovery on failure
- LiveCoordinator: discovery → queue → worker dispatch
- Recovery: WorkerRecovery, ProviderFailureRecovery, SchedulerRecovery, QueueRecovery
- Heartbeat: monitoring loop
- Publisher: event distribution
- LoggingContext: structured logging
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── Recovery Tests ─────────────────────────────────────────────────


class TestWorkerRecovery:
    """Test WorkerRecovery component."""

    def test_init_default(self) -> None:
        from app.live.recovery import WorkerRecovery

        recovery = WorkerRecovery()
        assert recovery.get_failed_workers() == {}

    def test_init_custom_policy(self) -> None:
        from app.live.recovery import RetryPolicy, WorkerRecovery

        policy = RetryPolicy(max_retries=5)
        recovery = WorkerRecovery(retry_policy=policy)
        assert recovery.get_failed_workers() == {}

    @pytest.mark.asyncio
    async def test_recover_success_first_try(self) -> None:
        from app.live.recovery import WorkerRecovery

        recovery = WorkerRecovery()
        restart_fn = AsyncMock(return_value=True)

        result = await recovery.recover("worker_1", restart_fn)

        assert result is True
        restart_fn.assert_called_once()
        assert recovery.get_failed_workers() == {}

    @pytest.mark.asyncio
    async def test_recover_success_after_retry(self) -> None:
        from app.live.recovery import RetryPolicy, WorkerRecovery

        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        recovery = WorkerRecovery(retry_policy=policy)

        call_count = 0

        async def flaky_restart() -> bool:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Temporary failure")
            return True

        result = await recovery.recover("worker_1", flaky_restart)

        assert result is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_recover_failure_after_max_retries(self) -> None:
        from app.live.recovery import RetryPolicy, WorkerRecovery

        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        recovery = WorkerRecovery(retry_policy=policy)

        async def always_fail() -> bool:
            raise RuntimeError("Permanent failure")

        result = await recovery.recover("worker_1", always_fail)

        assert result is False
        assert "worker_1" in recovery.get_failed_workers()


class TestProviderFailureRecovery:
    """Test ProviderFailureRecovery component."""

    @pytest.mark.asyncio
    async def test_recover_success(self) -> None:
        from app.live.recovery import ProviderFailureRecovery

        recovery = ProviderFailureRecovery()
        recovery_fn = AsyncMock(return_value=True)

        result = await recovery.recover("provider_1", recovery_fn)

        assert result is True
        recovery_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_recover_failure(self) -> None:
        from app.live.recovery import ProviderFailureRecovery, RetryPolicy

        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        recovery = ProviderFailureRecovery(retry_policy=policy)

        async def always_fail() -> bool:
            raise RuntimeError("Provider down")

        result = await recovery.recover("provider_1", always_fail)

        assert result is False


class TestSchedulerRecovery:
    """Test SchedulerRecovery component."""

    def test_init(self) -> None:
        from app.live.recovery import SchedulerRecovery

        recovery = SchedulerRecovery()
        assert recovery.is_degraded is False

    def test_record_success_resets_failures(self) -> None:
        from app.live.recovery import SchedulerRecovery

        recovery = SchedulerRecovery()
        recovery.record_failure()
        recovery.record_failure()
        assert recovery._consecutive_failures == 2
        recovery.record_success()
        assert recovery._consecutive_failures == 0

    def test_degraded_state(self) -> None:
        from app.live.recovery import SchedulerRecovery

        recovery = SchedulerRecovery()
        for _ in range(5):
            recovery.record_failure()
        assert recovery.is_degraded is True

    @pytest.mark.asyncio
    async def test_recover_success(self) -> None:
        from app.live.recovery import SchedulerRecovery

        recovery = SchedulerRecovery()
        restart_fn = AsyncMock(return_value=True)

        result = await recovery.recover("scheduler_1", restart_fn)

        assert result is True
        assert recovery._consecutive_failures == 0


class TestQueueRecovery:
    """Test QueueRecovery component."""

    @pytest.mark.asyncio
    async def test_recover_stuck_queue(self) -> None:
        from app.live.queue import MatchQueue
        from app.live.recovery import QueueRecovery

        queue = MatchQueue()
        recovery = QueueRecovery()

        result = await recovery.recover_stuck_queue(queue)

        assert result == 0

    @pytest.mark.asyncio
    async def test_validate_queue_healthy(self) -> None:
        from app.live.queue import MatchQueue
        from app.live.recovery import QueueRecovery

        queue = MatchQueue()
        recovery = QueueRecovery()

        is_healthy = await recovery.validate_queue(queue)

        assert is_healthy is True


class TestRetryPolicy:
    """Test RetryPolicy."""

    def test_initial_state(self) -> None:
        from app.live.recovery import RetryPolicy

        policy = RetryPolicy(max_retries=3, base_delay=1.0)
        assert policy.should_retry() is True
        assert policy.attempt == 0

    def test_get_delay(self) -> None:
        from app.live.recovery import RetryPolicy

        policy = RetryPolicy(max_retries=3, base_delay=1.0)
        assert policy.get_delay() == 1.0
        policy.record_attempt()
        assert policy.get_delay() == 2.0
        policy.record_attempt()
        assert policy.get_delay() == 4.0

    def test_max_delay_cap(self) -> None:
        from app.live.recovery import RetryPolicy

        policy = RetryPolicy(max_retries=10, base_delay=1.0, max_delay=5.0)
        for _ in range(10):
            policy.record_attempt()
        assert policy.get_delay() == 5.0

    def test_reset(self) -> None:
        from app.live.recovery import RetryPolicy

        policy = RetryPolicy(max_retries=3)
        policy.record_attempt()
        policy.record_attempt()
        assert policy.attempt == 2
        policy.reset()
        assert policy.attempt == 0
        assert policy.should_retry() is True


# ── Worker Tests ───────────────────────────────────────────────────


class TestLiveWorker:
    """Test LiveWorker component."""

    def test_init(self) -> None:
        from app.live.worker import LiveWorker

        worker = LiveWorker(worker_id="test_worker")
        assert worker.worker_id == "test_worker"
        assert worker.is_busy is False
        assert worker.processed_count == 0

    @pytest.mark.asyncio
    async def test_process_no_engines(self) -> None:
        from app.live.models import LiveMatch
        from app.live.worker import LiveWorker

        worker = LiveWorker(worker_id="test_worker")
        match = LiveMatch(fixture_id=123, home_team="Team A", away_team="Team B")

        events = await worker.process(match)

        assert events == []
        assert worker.processed_count == 1

    @pytest.mark.asyncio
    async def test_process_with_prediction_engine(self) -> None:
        from app.live.models import LiveMatch
        from app.live.worker import LiveWorker

        mock_prediction = MagicMock()
        mock_prediction.overall_confidence = 0.75

        mock_prediction_engine = AsyncMock()
        mock_prediction_engine.predict = AsyncMock(return_value=mock_prediction)

        mock_signal_engine = AsyncMock()
        mock_signal_engine.process = AsyncMock(return_value=[])

        worker = LiveWorker(
            worker_id="test_worker",
            prediction_engine=mock_prediction_engine,
            signal_engine=mock_signal_engine,
        )

        match = LiveMatch(fixture_id=123, home_team="Team A", away_team="Team B")

        events = await worker.process(match)

        assert len(events) >= 1
        assert events[0].event_type == "prediction_updated"

    @pytest.mark.asyncio
    async def test_process_callback(self) -> None:
        from app.live.models import LiveMatch
        from app.live.worker import LiveWorker

        callback = AsyncMock()
        worker = LiveWorker(worker_id="test_worker")
        worker.on_events(callback)

        match = LiveMatch(fixture_id=123)
        await worker.process(match)

        callback.assert_called_once()


# ── Coordinator Tests ──────────────────────────────────────────────


class TestLiveCoordinator:
    """Test LiveCoordinator component."""

    @pytest.mark.asyncio
    async def test_run_cycle_empty(self) -> None:
        from app.live.coordinator import LiveCoordinator
        from app.live.dispatcher import EventDispatcher
        from app.live.matcher import MatchDiscovery
        from app.live.publisher import EventPublisher
        from app.live.queue import MatchQueue
        from app.live.state import StateRegistry
        from app.live.worker import LiveWorker

        mock_discovery = AsyncMock(spec=MatchDiscovery)
        mock_discovery.discover = AsyncMock(return_value=[])

        queue = MatchQueue()
        state = StateRegistry()
        publisher = EventPublisher()
        dispatcher = EventDispatcher(publisher)
        worker = LiveWorker(worker_id="w1")

        coordinator = LiveCoordinator(
            discovery=mock_discovery,
            queue=queue,
            workers=[worker],
            dispatcher=dispatcher,
            state_registry=state,
        )

        await coordinator.run_cycle()

        assert queue.is_empty

    @pytest.mark.asyncio
    async def test_get_status(self) -> None:
        from app.live.coordinator import LiveCoordinator
        from app.live.dispatcher import EventDispatcher
        from app.live.matcher import MatchDiscovery
        from app.live.publisher import EventPublisher
        from app.live.queue import MatchQueue
        from app.live.state import StateRegistry
        from app.live.worker import LiveWorker

        mock_discovery = AsyncMock(spec=MatchDiscovery)
        queue = MatchQueue()
        state = StateRegistry()
        publisher = EventPublisher()
        dispatcher = EventDispatcher(publisher)
        worker = LiveWorker(worker_id="w1")

        coordinator = LiveCoordinator(
            discovery=mock_discovery,
            queue=queue,
            workers=[worker],
            dispatcher=dispatcher,
            state_registry=state,
        )

        status = coordinator.get_status()

        assert "running" in status
        assert "workers" in status
        assert status["workers"] == 1


# ── Publisher Tests ────────────────────────────────────────────────


class TestEventPublisher:
    """Test EventPublisher component."""

    def test_init(self) -> None:
        from app.live.publisher import EventPublisher

        publisher = EventPublisher()
        assert publisher.published_count == 0
        assert publisher.handler_count == 0

    def test_register_handler(self) -> None:
        from app.live.publisher import EventPublisher

        publisher = EventPublisher()
        handler = AsyncMock()
        publisher.register(handler)
        assert publisher.handler_count == 1

    def test_unregister_handler(self) -> None:
        from app.live.publisher import EventPublisher

        publisher = EventPublisher()
        handler = AsyncMock()
        publisher.register(handler)
        publisher.unregister(handler)
        assert publisher.handler_count == 0

    @pytest.mark.asyncio
    async def test_publish_event(self) -> None:
        from app.live.events import LiveEvent
        from app.live.publisher import EventPublisher

        publisher = EventPublisher()
        handler = AsyncMock()
        publisher.register(handler)

        event = LiveEvent(event_id="evt_1", event_type="test", fixture_id=1)
        await publisher.publish(event)

        handler.assert_called_once_with(event)
        assert publisher.published_count == 1

    @pytest.mark.asyncio
    async def test_publish_many(self) -> None:
        from app.live.events import LiveEvent
        from app.live.publisher import EventPublisher

        publisher = EventPublisher()
        handler = AsyncMock()
        publisher.register(handler)

        events = [
            LiveEvent(event_id=f"evt_{i}", event_type="test", fixture_id=1)
            for i in range(5)
        ]
        await publisher.publish_many(events)

        assert handler.call_count == 5
        assert publisher.published_count == 5

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_propagate(self) -> None:
        from app.live.events import LiveEvent
        from app.live.publisher import EventPublisher

        publisher = EventPublisher()

        async def failing_handler(event: LiveEvent) -> None:
            raise RuntimeError("Handler error")

        publisher.register(failing_handler)

        event = LiveEvent(event_id="evt_1", event_type="test", fixture_id=1)
        # Should not raise
        await publisher.publish(event)
        assert publisher.published_count == 1

    def test_get_recent_events(self) -> None:
        from app.live.events import LiveEvent
        from app.live.publisher import EventPublisher

        publisher = EventPublisher()
        events = [
            LiveEvent(event_id=f"evt_{i}", event_type="test", fixture_id=1)
            for i in range(10)
        ]

        for event in events:
            publisher._event_buffer.append(event)

        recent = publisher.get_recent_events(limit=5)
        assert len(recent) == 5


# ── Heartbeat Tests ────────────────────────────────────────────────


class TestHeartbeatMonitor:
    """Test HeartbeatMonitor component."""

    def test_init(self) -> None:
        from app.live.heartbeat import HeartbeatMonitor
        from app.live.state import StateRegistry

        state = StateRegistry()
        monitor = HeartbeatMonitor(state_registry=state)

        info = monitor.get_info()
        assert info.workers_healthy == 0
        assert info.workers_total == 0

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        from app.live.heartbeat import HeartbeatMonitor
        from app.live.state import StateRegistry

        state = StateRegistry()
        monitor = HeartbeatMonitor(state_registry=state, interval=0.1)

        await monitor.start()
        assert monitor._running is True

        await asyncio.sleep(0.05)

        await monitor.stop()
        assert monitor._running is False


# ── LoggingContext Tests ──────────────────────────────────────────


class TestLoggingContext:
    """Test LoggingContext helper."""

    def test_log_context_basic(self) -> None:
        from app.live.logging_context import LogContext

        ctx = LogContext(
            correlation_id="corr_1",
            worker_id="worker_1",
            match_id=123,
        )

        d = ctx.to_dict()
        assert d["correlation_id"] == "corr_1"
        assert d["worker_id"] == "worker_1"
        assert d["match_id"] == 123

    def test_log_context_context_manager(self) -> None:
        from app.live.logging_context import LogContext, get_current_context

        ctx = LogContext(correlation_id="corr_1", worker_id="worker_1")
        with ctx:
            current = get_current_context()
            assert current.correlation_id == "corr_1"
            assert current.worker_id == "worker_1"

        current = get_current_context()
        assert current.correlation_id is None
        assert current.worker_id is None

    def test_timer(self) -> None:
        from app.live.logging_context import Timer

        with Timer() as timer:
            pass

        assert timer.elapsed_ms >= 0

    def test_with_execution_time(self) -> None:
        from app.live.logging_context import LogContext

        ctx = LogContext(correlation_id="corr_1")
        ctx.with_execution_time(123.45)
        assert ctx.execution_time_ms == 123.45


# ── State Registry Tests ──────────────────────────────────────────


class TestStateRegistry:
    """Test StateRegistry component."""

    @pytest.mark.asyncio
    async def test_register_worker(self) -> None:
        from app.live.state import StateRegistry

        state = StateRegistry()
        await state.register_worker("worker_1")

        worker = await state.get_worker("worker_1")
        assert worker is not None
        assert worker.worker_id == "worker_1"

    @pytest.mark.asyncio
    async def test_get_all_workers(self) -> None:
        from app.live.state import StateRegistry

        state = StateRegistry()
        await state.register_worker("worker_1")
        await state.register_worker("worker_2")

        workers = await state.get_all_workers()
        assert len(workers) == 2

    @pytest.mark.asyncio
    async def test_update_match_state(self) -> None:
        from app.live.models import MatchState
        from app.live.state import StateRegistry

        state = StateRegistry()
        await state.update_match_state(123, MatchState.LIVE)

        match_state = await state.get_match_state(123)
        assert match_state == MatchState.LIVE

    def test_heartbeat(self) -> None:
        from app.live.state import StateRegistry

        state = StateRegistry()
        state.record_heartbeat()
        heartbeat = state.get_heartbeat()
        assert heartbeat.timestamp is not None


# ── Queue Tests ───────────────────────────────────────────────────


class TestMatchQueue:
    """Test MatchQueue component."""

    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self) -> None:
        from app.live.models import LiveMatch
        from app.live.queue import MatchQueue

        queue = MatchQueue()
        match = LiveMatch(fixture_id=123, home_team="A", away_team="B")

        await queue.enqueue(match)
        assert queue.size == 1

        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.fixture_id == 123
        assert queue.is_empty

    @pytest.mark.asyncio
    async def test_priority_queue(self) -> None:
        from app.live.models import LiveMatch
        from app.live.queue import MatchQueue

        queue = MatchQueue()
        normal = LiveMatch(fixture_id=100, home_team="A", away_team="B")
        priority = LiveMatch(fixture_id=200, home_team="C", away_team="D")

        await queue.enqueue(normal)
        await queue.enqueue_priority(priority)

        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.fixture_id == 200  # Priority first

    def test_get_stats(self) -> None:
        from app.live.queue import MatchQueue

        queue = MatchQueue()
        stats = queue.get_stats()
        assert stats["total"] == 0
        assert stats["priority"] == 0

    @pytest.mark.asyncio
    async def test_mark_processed(self) -> None:
        from app.live.models import LiveMatch
        from app.live.queue import MatchQueue

        queue = MatchQueue()
        match = LiveMatch(fixture_id=123)

        await queue.enqueue(match)
        await queue.mark_processed(123)

        # Dequeue the original entry
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.fixture_id == 123
        assert queue.is_empty

        # Re-enqueue should be skipped because fixture was already processed
        await queue.enqueue(match)
        assert queue.size == 0  # Confirms skip behavior

    @pytest.mark.asyncio
    async def test_clear_processed(self) -> None:
        from app.live.models import LiveMatch
        from app.live.queue import MatchQueue

        queue = MatchQueue()
        match = LiveMatch(fixture_id=123)

        await queue.enqueue(match)
        await queue.mark_processed(123)

        # Dequeue the original entry
        await queue.dequeue()
        assert queue.is_empty

        # Re-enqueue is skipped because fixture is in processed set
        await queue.enqueue(match)
        assert queue.size == 0

        # Clear processed IDs
        await queue.clear_processed()

        # Now re-enqueue should succeed
        await queue.enqueue(match)
        assert queue.size == 1
