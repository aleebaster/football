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
