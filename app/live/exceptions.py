"""Live Engine — custom exceptions for the Live Engine."""

from __future__ import annotations


class LiveEngineError(Exception):
    """Base exception for Live Engine errors."""

    def __init__(
        self, message: str = "", details: dict[str, object] | None = None
    ) -> None:
        super().__init__(message)
        self.details: dict[str, object] = details or {}


class WorkerError(LiveEngineError):
    """Raised when a worker encounters an error."""


class QueueError(LiveEngineError):
    """Raised when the queue encounters an error."""


class MatchDiscoveryError(LiveEngineError):
    """Raised when match discovery fails."""


class EventPublishError(LiveEngineError):
    """Raised when event publishing fails."""


class SchedulerError(LiveEngineError):
    """Raised when the scheduler encounters an error."""


class RecoveryError(LiveEngineError):
    """Raised when recovery fails."""


class MatchStateError(LiveEngineError):
    """Raised when an invalid state transition occurs."""
