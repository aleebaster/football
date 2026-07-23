"""Health DTO — system health status for API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProviderHealthDTO(BaseModel):
    """Health status of a data provider."""

    name: str
    status: str = "unknown"
    success_rate: float = Field(default=0.0, ge=0, le=1)
    avg_response_ms: float = Field(default=0.0, ge=0)
    consecutive_failures: int = Field(default=0, ge=0)


class CacheHealthDTO(BaseModel):
    """Health status of the cache layer."""

    backend: str = "memory"
    entries: int = Field(default=0, ge=0)
    hit_rate: float = Field(default=0.0, ge=0, le=1)


class EngineHealthDTO(BaseModel):
    """Health status of an engine."""

    name: str
    status: str = "unknown"
    uptime_seconds: float = Field(default=0.0, ge=0)
    last_activity: datetime | None = None


class HealthDTO(BaseModel):
    """Full system health status."""

    status: str = "healthy"
    version: str = "0.1.0"
    uptime_seconds: float = Field(default=0.0, ge=0)
    providers: list[ProviderHealthDTO] = Field(default_factory=list)
    cache: CacheHealthDTO = Field(default_factory=CacheHealthDTO)
    engines: list[EngineHealthDTO] = Field(default_factory=list)
    database: str = "connected"
    timestamp: datetime | None = None
