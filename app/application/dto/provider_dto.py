"""Provider DTO — provider data for API responses."""

from pydantic import BaseModel, Field


class ProviderDTO(BaseModel):
    """Provider data for API response."""

    name: str
    status: str = "unknown"
    priority: int = 50
    success_rate: float = Field(default=0.0, ge=0, le=1)
    avg_response_ms: float = Field(default=0.0, ge=0)
    total_requests: int = Field(default=0, ge=0)
    consecutive_failures: int = Field(default=0, ge=0)


class ProviderListDTO(BaseModel):
    """List of providers."""

    providers: list[ProviderDTO] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    healthy: int = Field(default=0, ge=0)
    degraded: int = Field(default=0, ge=0)
    unhealthy: int = Field(default=0, ge=0)
