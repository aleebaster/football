"""Pydantic models for Signal Engine."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.prediction.models import PredictionMarket, RiskLevel


class SignalType(StrEnum):
    """Signal types."""

    NEW = "new"
    UPDATE = "update"
    CANCEL = "cancel"
    CONFIDENCE_UP = "confidence_up"
    CONFIDENCE_DOWN = "confidence_down"
    RISK_CHANGE = "risk_change"
    MATCH_START = "match_start"
    LIVE = "live"
    MATCH_END = "match_end"


class SignalPriority(StrEnum):
    """Signal priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValueCategory(StrEnum):
    """Value signal categories."""

    STRONG_VALUE = "strong_value"
    VALUE = "value"
    NEUTRAL = "neutral"
    NEGATIVE_EV = "negative_ev"


class SignalStatus(StrEnum):
    """Signal status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class SignalRequest(BaseModel):
    """Request for signal generation."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    competition_id: int | None = None
    markets: list[PredictionMarket] | None = None
    force_refresh: bool = False


class SignalScore(BaseModel):
    """Comprehensive signal quality score."""

    overall: float = Field(default=0.5, ge=0, le=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    expected_value: float = Field(default=0.0, ge=-1, le=10)
    risk: float = Field(default=0.5, ge=0, le=1)
    data_quality: float = Field(default=0.5, ge=0, le=1)
    provider_quality: float = Field(default=0.5, ge=0, le=1)
    prediction_stability: float = Field(default=0.5, ge=0, le=1)
    historical_accuracy: float = Field(default=0.5, ge=0, le=1)
    market_quality: float = Field(default=0.5, ge=0, le=1)
    signal_freshness: float = Field(default=1.0, ge=0, le=1)
    factors: list[str] = Field(default_factory=list)


class SignalRank(BaseModel):
    """Signal ranking information."""

    position: int = 0
    percentile: float = Field(default=0.5, ge=0, le=1)
    comparison_score: float = Field(default=0.5, ge=0, le=1)


class Signal(BaseModel):
    """Signal generated from prediction result."""

    id: str = ""
    fixture_id: int
    home_team_id: int
    away_team_id: int
    competition_id: int | None = None

    # Signal details
    signal_type: SignalType = SignalType.NEW
    priority: SignalPriority = SignalPriority.MEDIUM
    status: SignalStatus = SignalStatus.ACTIVE
    market: PredictionMarket = PredictionMarket.MATCH_WINNER

    # Prediction data
    prediction_id: str = ""
    outcome: str = ""
    probability: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    odds: float = Field(default=1.0, gt=0)

    # Scoring
    score: SignalScore = Field(default_factory=SignalScore)
    rank: SignalRank = Field(default_factory=SignalRank)
    value_category: ValueCategory = ValueCategory.NEUTRAL

    # Risk
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = Field(default=0.5, ge=0, le=1)

    # Explanation
    summary: str = ""
    key_factors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Metadata
    model_version: str = "1.0.0"
    signal_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None


class SignalHistory(BaseModel):
    """Stored signal for historical tracking."""

    id: int | None = None
    signal_id: str
    fixture_id: int
    signal: Signal
    actual_outcome: str | None = None
    is_correct: bool | None = None
    roi: float = Field(default=0.0)
    edge: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None


class SignalNotification(BaseModel):
    """Notification decision for a signal."""

    signal_id: str
    signal_type: SignalType
    priority: SignalPriority
    should_notify: bool = False
    reason: str = ""
    notification_key: str = ""


class UserPreferences(BaseModel):
    """User signal preferences."""

    user_id: int
    favorite_teams: list[int] = Field(default_factory=list)
    favorite_leagues: list[int] = Field(default_factory=list)
    min_confidence: float = Field(default=0.5, ge=0, le=1)
    max_risk: RiskLevel = RiskLevel.HIGH
    allowed_markets: list[PredictionMarket] | None = None
    notification_start_hour: int = Field(default=8, ge=0, le=23)
    notification_end_hour: int = Field(default=23, ge=0, le=23)
    timezone: str = "UTC"
    language: str = "en"
    enabled: bool = True


class Watchlist(BaseModel):
    """User watchlist for filtering signals."""

    user_id: int
    teams: list[int] = Field(default_factory=list)
    leagues: list[int] = Field(default_factory=list)
    fixtures: list[int] = Field(default_factory=list)
    tournaments: list[int] = Field(default_factory=list)


class Portfolio(BaseModel):
    """User portfolio for tracking bets."""

    user_id: int
    active_bets: list[str] = Field(default_factory=list)
    total_stake: float = Field(default=0.0, ge=0)
    total_pnl: float = Field(default=0.0)
    win_count: int = Field(default=0, ge=0)
    loss_count: int = Field(default=0, ge=0)


class ROIStatistics(BaseModel):
    """ROI statistics for performance tracking."""

    market: PredictionMarket | None = None
    total_signals: int = Field(default=0, ge=0)
    winning_signals: int = Field(default=0, ge=0)
    losing_signals: int = Field(default=0, ge=0)
    roi: float = Field(default=0.0)
    yield_pct: float = Field(default=0.0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    average_odds: float = Field(default=1.0, ge=0)
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    average_risk: float = Field(default=0.0, ge=0, le=1)
    average_edge: float = Field(default=0.0)
    signal_accuracy: float = Field(default=0.0, ge=0, le=1)


class PerformanceStatistics(BaseModel):
    """Performance statistics by market type."""

    market: PredictionMarket
    total_signals: int = Field(default=0, ge=0)
    win_rate: float = Field(default=0.0, ge=0, le=1)
    roi: float = Field(default=0.0)
    average_confidence: float = Field(default=0.0, ge=0, le=1)
    average_edge: float = Field(default=0.0)


class SignalMetrics(BaseModel):
    """Metrics for signal engine monitoring."""

    total_processed: int = Field(default=0, ge=0)
    total_generated: int = Field(default=0, ge=0)
    total_filtered: int = Field(default=0, ge=0)
    total_duplicates: int = Field(default=0, ge=0)
    total_cooldown: int = Field(default=0, ge=0)
    avg_processing_time_ms: float = Field(default=0.0, ge=0)
    uptime_seconds: float = Field(default=0.0, ge=0)
    last_processed_at: datetime | None = None
