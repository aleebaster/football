"""Statistics DTO — statistics data for API responses."""

from pydantic import BaseModel, Field


class OverallStatisticsDTO(BaseModel):
    """Overall system statistics."""

    total_matches: int = Field(default=0, ge=0)
    total_predictions: int = Field(default=0, ge=0)
    total_signals: int = Field(default=0, ge=0)
    total_backtests: int = Field(default=0, ge=0)

    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    yield_pct: float = 0.0
    average_odds: float = Field(default=1.0, gt=0)
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    average_risk: float = Field(default=0.0, ge=0, le=1)

    brier_score: float = Field(default=0.0, ge=0)
    calibration_error: float = Field(default=0.0, ge=0, le=1)
    signal_accuracy: float = Field(default=0.0, ge=0, le=1)


class LeagueStatisticsDTO(BaseModel):
    """Statistics by league."""

    league_id: int
    league_name: str = ""
    total_matches: int = Field(default=0, ge=0)
    total_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    average_confidence: float = Field(default=0.0, ge=0, le=1)


class TeamStatisticsDTO(BaseModel):
    """Statistics by team."""

    team_id: int
    team_name: str = ""
    total_matches: int = Field(default=0, ge=0)
    total_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0


class MarketStatisticsDTO(BaseModel):
    """Statistics by market type."""

    market: str
    total_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    average_odds: float = Field(default=1.0, gt=0)
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    brier_score: float = Field(default=0.0, ge=0)
