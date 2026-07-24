"""Live Engine — Coordinator orchestrates the full Live Engine pipeline.

Pipeline:
    Scheduler → Discovery → Queue → Worker → Provider → AI → Prediction → Signal → Publisher
"""

from __future__ import annotations

import asyncio
import uuid

from app.live.dispatcher import EventDispatcher
from app.live.events import LiveEvent
from app.live.logging_context import LogContext, Timer, log_with_context
from app.live.matcher import MatchDiscovery
from app.live.models import LiveMatch, MatchState
from app.live.queue import MatchQueue
from app.live.state import StateRegistry
from app.live.worker import LiveWorker
from app.logging import get_logger

logger = get_logger(__name__)


class LiveCoordinator:
    """Orchestrates the full Live Engine pipeline.

    Responsibilities:
    - Discover matches via MatchDiscovery
    - Enqueue matches in the MatchQueue
    - Dispatch matches to idle Workers
    - Collect events and publish via the EventDispatcher
    """

    def __init__(
        self,
        discovery: MatchDiscovery,
        queue: MatchQueue,
        workers: list[LiveWorker],
        dispatcher: EventDispatcher,
        state_registry: StateRegistry,
        max_concurrent: int = 5,
    ) -> None:
        self._discovery = discovery
        self._queue = queue
        self._workers = workers
        self._dispatcher = dispatcher
        self._state_registry = state_registry
        self._max_concurrent = max_concurrent
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the coordinator."""
        self._running = True
        for worker in self._workers:
            await worker.start()
        self._state_registry.set_scheduler_running(True)
        logger.info(
            f"Live Coordinator started ({len(self._workers)} workers, max_concurrent={self._max_concurrent})"
        )

    async def stop(self) -> None:
        """Stop the coordinator."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        for worker in self._workers:
            await worker.stop()
        self._state_registry.set_scheduler_running(False)
        logger.info("Live Coordinator stopped")

    async def run_cycle(self) -> None:
        """Run a single discovery → process cycle."""
        ctx = LogContext(correlation_id=f"coord_{uuid.uuid4().hex[:8]}")

        with ctx:
            with Timer() as timer:
                try:
                    # Step 1: Discover matches
                    discovery_timer = Timer()
                    with discovery_timer:
                        matches = await self._discovery.discover()

                    log_with_context(
                        logger,
                        "debug",
                        f"Discovery found {len(matches)} matches in {discovery_timer.elapsed_ms:.1f}ms",
                    )

                    # Step 2: Enqueue discovered matches
                    for match in matches:
                        await self._state_registry.store_match(match)
                        if match.state in (
                            MatchState.LIVE,
                            MatchState.HALF_TIME,
                            MatchState.SECOND_HALF,
                        ):
                            await self._queue.enqueue_priority(match)
                        else:
                            await self._queue.enqueue(match)

                    # Step 3: Dispatch matches to idle workers
                    await self._dispatch_to_workers()

                except Exception as e:
                    log_with_context(
                        logger, "warning", f"Coordinator cycle failed: {e}"
                    )

            log_with_context(
                logger,
                "debug",
                f"Coordinator cycle completed in {timer.elapsed_ms:.1f}ms",
            )

    async def _dispatch_to_workers(self) -> None:
        """Dispatch queued matches to idle workers."""
        idle_workers = [w for w in self._workers if not w.is_busy]

        while idle_workers and not self._queue.is_empty:
            match = await self._queue.dequeue()
            if match is None:
                break

            worker = idle_workers.pop(0)
            asyncio.create_task(self._process_with_worker(worker, match))

    async def _process_with_worker(self, worker: LiveWorker, match: LiveMatch) -> None:
        """Process a match with a specific worker and publish events."""
        ctx = LogContext(
            worker_id=worker.worker_id,
            match_id=match.fixture_id,
        )

        with ctx:
            try:
                events = await worker.process(match)
                if events:
                    await self._dispatcher.dispatch_many(events)
                    for _ in events:
                        self._state_registry.increment_events_published()

                # Mark as processed in queue
                await self._queue.mark_processed(match.fixture_id)

            except Exception as e:
                log_with_context(
                    logger,
                    "warning",
                    f"Worker {worker.worker_id} failed on fixture {match.fixture_id}: {e}",
                )

    async def process_single(self, match: LiveMatch) -> list[LiveEvent]:
        """Process a single match immediately (bypasses queue)."""
        # Find an idle worker
        for worker in self._workers:
            if not worker.is_busy:
                events = await worker.process(match)
                if events:
                    await self._dispatcher.dispatch_many(events)
                    for _ in events:
                        self._state_registry.increment_events_published()
                return events

        # No idle workers — process in queue
        await self._queue.enqueue_priority(match)
        return []

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        return self._queue.size

    def get_status(self) -> dict[str, object]:
        """Get coordinator status."""
        return {
            "running": self._running,
            "queue_size": self._queue.size,
            "workers": len(self._workers),
            "busy_workers": len([w for w in self._workers if w.is_busy]),
        }
