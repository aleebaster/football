"""Backtesting Models — Pydantic models for the backtesting platform."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.prediction.models import PredictionMarket


class BacktestStatus(StrEnum):
    """Backtest execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestScope(StrEnum):
    """Scope of backtest execution."""

    SINGLE_MATCH = "single_match"
    DATE_RANGE = "date_range"
    LEAGUE = "league"
    SEASON = "season"
    TOURNAMENT = "tournament"
    ALL = "all"


class ExportFormat(StrEnum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class BacktestRequest(BaseModel):
    """Request for backtest execution."""

    scope: BacktestScope = BacktestScope.SINGLE_MATCH
    fixture_id: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    league_id: int | None = None
    season: int | None = None
    max_matches: int = Field(default=1000, ge=1)
    parallel: bool = False
    force_refresh: bool = False
    ai_version: str = "1.0.0"
    prediction_version: str = "1.0.0"
    signal_version: str = "1.0.0"


class EvaluationResult(BaseModel):
    """Result of evaluating a single prediction."""

    fixture_id: int
    market: PredictionMarket
    predicted_outcome: str
    predicted_probability: float = Field(ge=0, le=1)
    actual_outcome: str
    is_correct: bool
    odds: float = Field(default=1.0, gt=0)
    stake: float = Field(default=1.0, ge=0)
    pnl: float = 0.0
    roi: float = 0.0
    edge: float = 0.0
    expected_value: float = 0.0
    confidence: float = Field(default=0.5, ge=0, le=1)
    risk_score: float = Field(default=0.5, ge=0, le=1)
    signal_id: str = ""
    model_version: str = "1.0.0"
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BacktestMetrics(BaseModel):
    """Aggregate metrics from backtest results."""

    total_predictions: int = Field(default=0, ge=0)
    correct_predictions: int = Field(default=0, ge=0)
    incorrect_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    loss_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    yield_pct: float = 0.0
    total_stake: float = Field(default=0.0, ge=0)
    total_pnl: float = 0.0
    average_odds: float = Field(default=1.0, gt=0)
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    average_risk: float = Field(default=0.0, ge=0, le=1)
    average_edge: float = 0.0
    average_ev: float = 0.0
    accuracy: float = Field(default=0.0, ge=0, le=1)
    precision: float = Field(default=0.0, ge=0, le=1)
    recall: float = Field(default=0.0, ge=0, le=1)
    f1_score: float = Field(default=0.0, ge=0, le=1)
    brier_score: float = Field(default=0.0, ge=0)
    log_loss: float = Field(default=0.0, ge=0)
    calibration_error: float = Field(default=0.0, ge=0, le=1)
    prediction_stability: float = Field(default=0.0, ge=0, le=1)
    signal_accuracy: float = Field(default=0.0, ge=0, le=1)
    best_market: PredictionMarket | None = None
    worst_market: PredictionMarket | None = None


class MarketBreakdown(BaseModel):
    """Metrics broken down by market."""

    market: PredictionMarket
    total: int = Field(default=0, ge=0)
    correct: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    average_odds: float = Field(default=1.0, gt=0)
    average_confidence: float = Field(default=0.0, ge=0, le=1)


class CalibrationBucket(BaseModel):
    """Calibration bucket for a probability range."""

    lower: float
    upper: float
    count: int = Field(default=0, ge=0)
    correct: int = Field(default=0, ge=0)
    observed_frequency: float = Field(default=0.0, ge=0, le=1)
    expected_frequency: float = Field(default=0.0, ge=0, le=1)
    gap: float = 0.0


# ── Per-entity statistics (spec-required) ────────────────────────────


class LeagueStatistics(BaseModel):
    """Statistics aggregated by league."""

    league_id: int
    league_name: str = ""
    total_matches: int = Field(default=0, ge=0)
    total_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    average_odds: float = Field(default=1.0, gt=0)


class SeasonStatistics(BaseModel):
    """Statistics aggregated by season."""

    season: int
    total_matches: int = Field(default=0, ge=0)
    total_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    average_confidence: float = Field(default=0.0, ge=0, le=1)


class TeamStatistics(BaseModel):
    """Statistics aggregated by team."""

    team_id: int
    team_name: str = ""
    total_matches: int = Field(default=0, ge=0)
    total_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0


class PredictionStatistics(BaseModel):
    """Statistics aggregated by prediction type/market."""

    market: PredictionMarket
    total_predictions: int = Field(default=0, ge=0)
    correct_predictions: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    average_odds: float = Field(default=1.0, gt=0)
    brier_score: float = Field(default=0.0, ge=0)


class SignalStatistics(BaseModel):
    """Statistics aggregated by signal type."""

    signal_type: str = ""
    total_signals: int = Field(default=0, ge=0)
    winning_signals: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = 0.0
    average_confidence: float = Field(default=0.0, ge=0, le=1)


# ── Backtest summary & result ────────────────────────────────────────


class BacktestSummary(BaseModel):
    """Summary of backtest results."""

    request: BacktestRequest
    status: BacktestStatus
    metrics: BacktestMetrics
    market_breakdown: list[MarketBreakdown] = Field(default_factory=list)
    calibration_buckets: list[CalibrationBucket] = Field(default_factory=list)
    league_statistics: list[LeagueStatistics] = Field(default_factory=list)
    season_statistics: list[SeasonStatistics] = Field(default_factory=list)
    team_statistics: list[TeamStatistics] = Field(default_factory=list)
    prediction_statistics: list[PredictionStatistics] = Field(default_factory=list)
    signal_statistics: list[SignalStatistics] = Field(default_factory=list)
    total_evaluations: int = Field(default=0, ge=0)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    duration_seconds: float = 0.0


class ComparisonResult(BaseModel):
    """Result of comparing two backtest runs."""

    version_a: str
    version_b: str
    metrics_a: BacktestMetrics
    metrics_b: BacktestMetrics
    improvement: dict[str, float] = Field(default_factory=dict)
    regressions: dict[str, float] = Field(default_factory=dict)
    summary: str = ""


class BacktestResult(BaseModel):
    """Complete backtest result with all data."""

    id: str = ""
    request: BacktestRequest
    status: BacktestStatus = BacktestStatus.PENDING
    evaluations: list[EvaluationResult] = Field(default_factory=list)
    metrics: BacktestMetrics = Field(default_factory=BacktestMetrics)
    summary: BacktestSummary | None = None
    ai_version: str = "1.0.0"
    prediction_version: str = "1.0.0"
    signal_version: str = "1.0.0"
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    error: str | None = None


class CalibrationDataset(BaseModel):
    """Dataset for model calibration training."""

    id: str = ""
    fixture_id: int
    market: PredictionMarket
    predicted_probability: float = Field(ge=0, le=1)
    actual_outcome: bool
    odds: float = Field(default=1.0, gt=0)
    confidence: float = Field(default=0.5, ge=0, le=1)
    features: dict[str, float] = Field(default_factory=dict)
    model_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
