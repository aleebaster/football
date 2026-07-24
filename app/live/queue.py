"""Live Engine — Match Queue for ordered processing.

The Queue is responsible only for the order of match processing.
It contains no business logic.
"""

from __future__ import annotations

import asyncio
from collections import deque

from app.live.exceptions import QueueError
from app.live.models import LiveMatch
from app.logging import get_logger

logger = get_logger(__name__)


class MatchQueue:
    """Thread-safe match processing queue.

    Maintains FIFO order for match processing.
    Supports priority insertion for urgent matches (e.g., goals, odds changes).
    """

    def __init__(self, max_size: int = 1000) -> None:
        self._queue: deque[LiveMatch] = deque()
        self._priority_queue: deque[LiveMatch] = deque()
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._processed_ids: set[int] = set()

    async def enqueue(self, match: LiveMatch) -> None:
        """Add a match to the processing queue."""
        async with self._lock:
            if match.fixture_id in self._processed_ids:
                logger.debug(f"Fixture {match.fixture_id} already processed, skipping")
                return
            if len(self._queue) >= self._max_size:
                raise QueueError(
                    f"Queue full ({self._max_size} max)",
                    details={"fixture_id": match.fixture_id},
                )
            self._queue.append(match)
            logger.debug(
                f"Enqueued fixture {match.fixture_id} (queue size: {len(self._queue)})"
            )

    async def enqueue_priority(self, match: LiveMatch) -> None:
        """Add a match to the priority processing queue."""
        async with self._lock:
            self._priority_queue.append(match)
            logger.debug(f"Priority enqueued fixture {match.fixture_id}")

    async def dequeue(self) -> LiveMatch | None:
        """Get the next match to process. Priority queue takes precedence."""
        async with self._lock:
            if self._priority_queue:
                return self._priority_queue.popleft()
            if self._queue:
                return self._queue.popleft()
            return None

    async def mark_processed(self, fixture_id: int) -> None:
        """Mark a fixture as processed."""
        async with self._lock:
            self._processed_ids.add(fixture_id)

    async def clear_processed(self) -> None:
        """Clear the processed IDs set to allow reprocessing."""
        async with self._lock:
            self._processed_ids.clear()

    @property
    def size(self) -> int:
        """Current queue size (priority + normal)."""
        return len(self._priority_queue) + len(self._queue)

    @property
    def priority_size(self) -> int:
        """Current priority queue size."""
        return len(self._priority_queue)

    @property
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self.size == 0

    async def peek(self) -> LiveMatch | None:
        """Preview the next match without removing it."""
        async with self._lock:
            if self._priority_queue:
                return self._priority_queue[0]
            if self._queue:
                return self._queue[0]
            return None

    async def clear(self) -> None:
        """Clear all pending matches."""
        async with self._lock:
            self._queue.clear()
            self._priority_queue.clear()
            logger.info("Queue cleared")

    def get_stats(self) -> dict[str, int]:
        """Get queue statistics."""
        return {
            "total": self.size,
            "priority": self.priority_size,
            "normal": len(self._queue),
            "processed": len(self._processed_ids),
        }
