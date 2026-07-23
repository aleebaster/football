"""Prediction DTO — prediction data for API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class PredictionSummaryDTO(BaseModel):
    """Lightweight prediction summary."""

    fixture_id: int
    home_team: str = ""
    away_team: str = ""
    home_win_pct: float = Field(default=0.0, ge=0, le=1)
    draw_pct: float = Field(default=0.0, ge=0, le=1)
    away_win_pct: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)
    risk_level: str = "medium"
    computed_at: datetime | None = None


class ValueBetDTO(BaseModel):
    """Value bet recommendation."""

    market: str
    outcome: str
    model_probability: float = Field(ge=0, le=1)
    market_odds: float = Field(gt=1.0)
    edge: float = Field(default=0.0)
    expected_value: float = Field(default=0.0)
    explanation: str = ""


class PredictionDTO(BaseModel):
    """Full prediction data for API response."""

    fixture_id: int
    home_team: str = ""
    away_team: str = ""
    home_team_id: int | None = None
    away_team_id: int | None = None

    # Market predictions
    match_winner: dict[str, float] = Field(default_factory=dict)
    over_under_25: dict[str, float] = Field(default_factory=dict)
    btts: dict[str, float] = Field(default_factory=dict)

    # Overall
    overall_confidence: float = Field(default=0.0, ge=0, le=1)
    overall_risk_level: str = "medium"
    overall_risk_score: float = Field(default=0.0, ge=0, le=1)

    # Value bets
    value_bets: list[ValueBetDTO] = Field(default_factory=list)

    # Explanation
    summary: str = ""
    key_factors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Metadata
    model_version: str = "1.0.0"
    prediction_time_ms: float = 0.0
    computed_at: datetime | None = None
