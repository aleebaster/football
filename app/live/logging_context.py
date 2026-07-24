"""Live Engine — Structured logging context for observability.

Provides a context manager and helper for injecting structured fields
into log messages consistently across all Live Engine components.

Fields:
    - Correlation ID: traces a request across components
    - Worker ID: identifies which worker is processing
    - Match ID (Fixture ID): identifies which match is being processed
    - Execution Time: tracks how long an operation took
    - Provider Time: tracks provider response time
    - Scheduler Cycle: identifies which scheduler cycle is running
    - Event ID: identifies which event is being processed
"""

from __future__ import annotations

import contextvars
import time
from dataclasses import dataclass, field
from typing import Any

# Context variables for structured logging
_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)
_worker_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "worker_id", default=None
)
_match_id: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "match_id", default=None
)
_event_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "event_id", default=None
)
_scheduler_cycle: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "scheduler_cycle", default=None
)


@dataclass
class LogContext:
    """Structured logging context for the Live Engine.

    Usage:
        ctx = LogContext(correlation_id="abc123", worker_id="worker_0", match_id=12345)
        with ctx:
            logger.info("Processing match")  # Fields automatically injected

    Or manually:
        logger.info("Processing match", extra=ctx.to_dict())
    """

    correlation_id: str | None = None
    worker_id: str | None = None
    match_id: int | None = None
    event_id: str | None = None
    scheduler_cycle: str | None = None
    execution_time_ms: float | None = None
    provider_time_ms: float | None = None

    _tokens: dict[str, Any] = field(default_factory=dict, repr=False)

    def __enter__(self) -> LogContext:
        """Set context variables."""
        if self.correlation_id is not None:
            self._tokens["correlation_id"] = _correlation_id.set(self.correlation_id)
        if self.worker_id is not None:
            self._tokens["worker_id"] = _worker_id.set(self.worker_id)
        if self.match_id is not None:
            self._tokens["match_id"] = _match_id.set(self.match_id)
        if self.event_id is not None:
            self._tokens["event_id"] = _event_id.set(self.event_id)
        if self.scheduler_cycle is not None:
            self._tokens["scheduler_cycle"] = _scheduler_cycle.set(self.scheduler_cycle)
        return self

    def __exit__(self, *args: object) -> None:
        """Reset context variables."""
        for var_name, token in self._tokens.items():
            if var_name == "correlation_id":
                _correlation_id.reset(token)
            elif var_name == "worker_id":
                _worker_id.reset(token)
            elif var_name == "match_id":
                _match_id.reset(token)
            elif var_name == "event_id":
                _event_id.reset(token)
            elif var_name == "scheduler_cycle":
                _scheduler_cycle.reset(token)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to a dict for logger extra fields."""
        result: dict[str, Any] = {}
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.worker_id:
            result["worker_id"] = self.worker_id
        if self.match_id is not None:
            result["match_id"] = self.match_id
        if self.event_id:
            result["event_id"] = self.event_id
        if self.scheduler_cycle:
            result["scheduler_cycle"] = self.scheduler_cycle
        if self.execution_time_ms is not None:
            result["execution_time_ms"] = self.execution_time_ms
        if self.provider_time_ms is not None:
            result["provider_time_ms"] = self.provider_time_ms
        return result

    def with_execution_time(self, elapsed_ms: float) -> LogContext:
        """Return a copy with execution time set."""
        self.execution_time_ms = elapsed_ms
        return self

    def with_provider_time(self, elapsed_ms: float) -> LogContext:
        """Return a copy with provider time set."""
        self.provider_time_ms = elapsed_ms
        return self


def get_current_context() -> LogContext:
    """Get the current logging context from context variables."""
    return LogContext(
        correlation_id=_correlation_id.get(),
        worker_id=_worker_id.get(),
        match_id=_match_id.get(),
        event_id=_event_id.get(),
        scheduler_cycle=_scheduler_cycle.get(),
    )


def log_with_context(
    logger: Any,
    level: str,
    message: str,
    **extra_fields: Any,
) -> None:
    """Log a message with the current context fields.

    Args:
        logger: Logger instance.
        level: Log level (info, warning, error, debug).
        message: Log message.
        **extra_fields: Additional fields to include.
    """
    ctx = get_current_context()
    context_dict = ctx.to_dict()
    context_dict.update(extra_fields)

    log_func = getattr(logger, level, logger.info)
    if context_dict:
        log_func(f"{message} | {context_dict}")
    else:
        log_func(message)


class Timer:
    """Simple timer for measuring execution time."""

    def __init__(self) -> None:
        self._start: float = 0.0
        self._elapsed_ms: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self._elapsed_ms = (time.perf_counter() - self._start) * 1000

    @property
    def elapsed_ms(self) -> float:
        """Elapsed time in milliseconds."""
        return self._elapsed_ms

    @property
    def elapsed_seconds(self) -> float:
        """Elapsed time in seconds."""
        return self._elapsed_ms / 1000
