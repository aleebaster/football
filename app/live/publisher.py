"""Live Engine — Publisher for broadcasting events to all subscribers.

The Publisher does NOT know about any Engine.
It only distributes events to registered handlers (REST, Dashboard, Telegram, WebSocket).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from app.live.events import LiveEvent
from app.logging import get_logger

logger = get_logger(__name__)

EventHandler = Callable[[LiveEvent], Coroutine[Any, Any, None]]


class EventPublisher:
    """Publishes live events to all registered handlers.

    Supports:
    - REST API (polling)
    - Dashboard (future WebSocket)
    - Telegram (via adapter)
    - WebSocket (prepared, not implemented)
    """

    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []
        self._event_buffer: list[LiveEvent] = []
        self._max_buffer_size: int = 500
        self._published_count: int = 0

    def register(self, handler: EventHandler) -> None:
        """Register an event handler."""
        self._handlers.append(handler)
        logger.debug(
            f"Registered event handler: {getattr(handler, '__qualname__', type(handler).__name__)}"
        )

    def unregister(self, handler: EventHandler) -> None:
        """Unregister an event handler."""
        self._handlers = [h for h in self._handlers if h is not handler]

    async def publish(self, event: LiveEvent) -> None:
        """Publish a single event to all handlers."""
        self._event_buffer.append(event)
        if len(self._event_buffer) > self._max_buffer_size:
            self._event_buffer = self._event_buffer[-self._max_buffer_size :]

        self._published_count += 1

        tasks = [self._safe_call(handler, event) for handler in self._handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def publish_many(self, events: list[LiveEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)

    async def _safe_call(self, handler: EventHandler, event: LiveEvent) -> None:
        """Call a handler safely, catching exceptions."""
        try:
            await handler(event)
        except Exception as e:
            logger.warning(
                f"Handler {getattr(handler, '__qualname__', type(handler).__name__)} failed for {event.event_type}: {e}"
            )

    def get_recent_events(self, limit: int = 50) -> list[LiveEvent]:
        """Get recent events from the buffer."""
        return self._event_buffer[-limit:]

    @property
    def published_count(self) -> int:
        return self._published_count

    @property
    def handler_count(self) -> int:
        return len(self._handlers)
