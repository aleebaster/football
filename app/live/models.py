"""Live Engine — Pydantic models for the Live Engine.

All models use Pydantic for serialization, validation, and consistency.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MatchState(StrEnum):
    """Lifecycle states for a live match."""

    SCHEDULED = "scheduled"
    PREPARING = "preparing"
    STARTING = "starting"
    LIVE = "live"
    HALF_TIME = "half_time"
    SECOND_HALF = "second_half"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    INTERRUPTED = "interrupted"


class EventType(StrEnum):
    """Types of live events."""

    MATCH_STARTED = "match_started"
    PREDICTION_UPDATED = "prediction_updated"
    SIGNAL_CREATED = "signal_created"
    SIGNAL_UPDATED = "signal_updated"
    GOAL = "goal"
    ODDS_CHANGED = "odds_changed"
    MATCH_FINISHED = "match_finished"
    HEARTBEAT = "heartbeat"
    STATE_CHANGED = "state_changed"
    ERROR = "error"


class WorkerStatus(StrEnum):
    """Worker status."""

    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPED = "stopped"


class LiveMatch(BaseModel):
    """A match being tracked by the Live Engine."""

    fixture_id: int
    home_team_id: int = 0
    home_team: str = ""
    away_team_id: int = 0
    away_team: str = ""
    competition_id: int | None = None
    competition_name: str | None = None
    utc_date: datetime | None = None
    status: str = "SCHEDULED"
    state: MatchState = MatchState.SCHEDULED
    home_score: int | None = None
    away_score: int | None = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    extra_data: dict[str, Any] = Field(default_factory=dict)


class LiveEvent(BaseModel):
    """An event emitted by the Live Engine."""

    event_id: str = ""
    event_type: EventType
    fixture_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    worker_id: str | None = None


class MatchStartedEvent(LiveEvent):
    """Emitted when a match transitions to LIVE."""

    event_type: EventType = EventType.MATCH_STARTED


class PredictionUpdatedEvent(LiveEvent):
    """Emitted when predictions are updated for a live match."""

    event_type: EventType = EventType.PREDICTION_UPDATED


class SignalCreatedEvent(LiveEvent):
    """Emitted when a new signal is created for a live match."""

    event_type: EventType = EventType.SIGNAL_CREATED


class SignalUpdatedEvent(LiveEvent):
    """Emitted when a signal is updated."""

    event_type: EventType = EventType.SIGNAL_UPDATED


class GoalEvent(LiveEvent):
    """Emitted when a goal is scored."""

    event_type: EventType = EventType.GOAL


class OddsChangedEvent(LiveEvent):
    """Emitted when odds change significantly."""

    event_type: EventType = EventType.ODDS_CHANGED


class MatchFinishedEvent(LiveEvent):
    """Emitted when a match finishes."""

    event_type: EventType = EventType.MATCH_FINISHED


class HeartbeatEvent(LiveEvent):
    """Periodic heartbeat event for health monitoring."""

    event_type: EventType = EventType.HEARTBEAT


class WorkerInfo(BaseModel):
    """Information about a worker."""

    worker_id: str
    status: WorkerStatus = WorkerStatus.IDLE
    current_fixture_id: int | None = None
    processed_count: int = 0
    error_count: int = 0
    last_active: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float = 0.0


class LiveMetrics(BaseModel):
    """Metrics for the Live Engine."""

    active_matches: int = 0
    total_matches_processed: int = 0
    workers_active: int = 0
    workers_total: int = 0
    queue_size: int = 0
    events_published: int = 0
    provider_latency_ms: float = 0.0
    avg_prediction_time_ms: float = 0.0
    avg_signal_time_ms: float = 0.0
    last_heartbeat: datetime | None = None
    uptime_seconds: float = 0.0


class HeartbeatInfo(BaseModel):
    """Heartbeat status information."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    scheduler_running: bool = False
    workers_healthy: int = 0
    workers_total: int = 0
    provider_healthy: bool = False
    queue_size: int = 0
    uptime_seconds: float = 0.0
