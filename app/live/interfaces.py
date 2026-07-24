"""Live Engine — abstract interfaces for all Live Engine components.

Every component implements a protocol/interface for testability and DI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.live.events import LiveEvent
    from app.live.models import LiveMatch, MatchState


class MatchDiscoveryInterface(ABC):
    """Interface for discovering upcoming and live matches."""

    @abstractmethod
    async def discover(self) -> list[LiveMatch]:
        """Discover matches that need processing."""
        ...

    @abstractmethod
    async def get_live_matches(self) -> list[LiveMatch]:
        """Get currently live matches."""
        ...


class WorkerInterface(ABC):
    """Interface for a match processing worker."""

    @abstractmethod
    async def process(self, match: LiveMatch) -> list[LiveEvent]:
        """Process a single match through the full pipeline."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the worker."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the worker."""
        ...

    @property
    @abstractmethod
    def is_busy(self) -> bool:
        """Check if the worker is currently processing a match."""
        ...


class PublisherInterface(ABC):
    """Interface for event publishing."""

    @abstractmethod
    async def publish(self, event: LiveEvent) -> None:
        """Publish a single event."""
        ...

    @abstractmethod
    async def publish_many(self, events: list[LiveEvent]) -> None:
        """Publish multiple events."""
        ...


class DispatcherInterface(ABC):
    """Interface for event dispatching to channels."""

    @abstractmethod
    async def dispatch(self, event: LiveEvent) -> None:
        """Dispatch an event to all registered channels."""
        ...


class StateTrackerInterface(ABC):
    """Interface for tracking match state."""

    @abstractmethod
    async def update_state(self, fixture_id: int, state: MatchState) -> None:
        """Update the state of a match."""
        ...

    @abstractmethod
    async def get_state(self, fixture_id: int) -> MatchState | None:
        """Get the current state of a match."""
        ...

    @abstractmethod
    async def get_all_active(self) -> dict[int, MatchState]:
        """Get all active match states."""
        ...
