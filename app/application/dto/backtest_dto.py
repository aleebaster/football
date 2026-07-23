"""Backtest DTO — backtest data for API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class BacktestSummaryDTO(BaseModel):
    """Backtest summary for API response."""

    id: str = ""
    scope: str = "single_match"
    status: str = "completed"

    # Metrics
    total_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    yield_pct: float = 0.0
    average_odds: float = Field(default=1.0, gt=0)
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    brier_score: float = Field(default=0.0, ge=0)

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float = 0.0


class BacktestDTO(BaseModel):
    """Full backtest data for API response."""

    id: str = ""
    scope: str = "single_match"
    status: str = "pending"

    # Request
    fixture_id: int | None = None
    league_id: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    max_matches: int = 1000

    # Results
    total_evaluations: int = Field(default=0, ge=0)
    summary: BacktestSummaryDTO | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    error: str | None = None
