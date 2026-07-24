"""Live Engine — Dispatcher for routing events to channels.

The Dispatcher routes events to the appropriate channels
(REST polling, Dashboard, Telegram adapter, WebSocket).
"""

from __future__ import annotations

from app.live.events import LiveEvent
from app.live.publisher import EventPublisher
from app.logging import get_logger

logger = get_logger(__name__)


class EventDispatcher:
    """Dispatches events through the Publisher to all registered channels."""

    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher

    async def dispatch(self, event: LiveEvent) -> None:
        """Dispatch a single event through the publisher."""
        await self._publisher.publish(event)

    async def dispatch_many(self, events: list[LiveEvent]) -> None:
        """Dispatch multiple events."""
        await self._publisher.publish_many(events)
