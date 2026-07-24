"""Live DTOs — Data Transfer Objects for the Live Engine API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LiveMatchDTO(BaseModel):
    """Live match data for API response."""

    fixture_id: int
    home_team: str = ""
    away_team: str = ""
    competition_name: str | None = None
    status: str = "SCHEDULED"
    state: str = "scheduled"
    home_score: int | None = None
    away_score: int | None = None
    utc_date: datetime | None = None
    last_updated: datetime | None = None


class LiveEventDTO(BaseModel):
    """Live event data for API response."""

    event_id: str
    event_type: str
    fixture_id: int
    timestamp: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    worker_id: str | None = None


class WorkerDTO(BaseModel):
    """Worker data for API response."""

    worker_id: str
    status: str = "idle"
    current_fixture_id: int | None = None
    processed_count: int = 0
    error_count: int = 0
    last_active: datetime | None = None


class HeartbeatDTO(BaseModel):
    """Heartbeat data for API response."""

    timestamp: datetime
    scheduler_running: bool = False
    workers_healthy: int = 0
    workers_total: int = 0
    provider_healthy: bool = False
    queue_size: int = 0
    uptime_seconds: float = 0.0


class LiveMetricsDTO(BaseModel):
    """Live metrics data for API response."""

    active_matches: int = 0
    workers_active: int = 0
    workers_total: int = 0
    queue_size: int = 0
    events_published: int = 0
    provider_latency_ms: float = 0.0
    avg_prediction_time_ms: float = 0.0
    avg_signal_time_ms: float = 0.0
    uptime_seconds: float = 0.0


class LiveStatusDTO(BaseModel):
    """Overall live engine status for API response."""

    running: bool = False
    active_matches: int = 0
    workers_active: int = 0
    workers_total: int = 0
    queue_size: int = 0
    events_published: int = 0
    uptime_seconds: float = 0.0
