"""Signal DTO — signal data for API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class SignalDTO(BaseModel):
    """Signal data for API response."""

    id: str
    fixture_id: int
    home_team: str = ""
    away_team: str = ""

    # Signal details
    signal_type: str = "new"
    priority: str = "medium"
    status: str = "active"
    market: str = "match_winner"

    # Prediction data
    outcome: str = ""
    probability: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    odds: float = Field(default=1.0, gt=0)

    # Score
    overall_score: float = Field(default=0.5, ge=0, le=1)
    expected_value: float = Field(default=0.0)
    value_category: str = "neutral"

    # Risk
    risk_level: str = "medium"
    risk_score: float = Field(default=0.5, ge=0, le=1)

    # Summary
    summary: str = ""
    key_factors: list[str] = Field(default_factory=list)

    # Metadata
    model_version: str = "1.0.0"
    created_at: datetime | None = None
    expires_at: datetime | None = None


class SignalListDTO(BaseModel):
    """Paginated list of signals."""

    signals: list[SignalDTO] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)
