"""Pydantic models for Prediction Engine."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PredictionMarket(StrEnum):
    """Supported prediction markets."""

    MATCH_WINNER = "match_winner"
    DOUBLE_CHANCE = "double_chance"
    OVER_UNDER_25 = "over_under_25"
    BTTS = "btts"
    ASIAN_HANDICAP = "asian_handicap"
    CORNERS = "corners"
    CARDS = "cards"
    FIRST_GOAL = "first_goal"
    HALFTIME = "halftime"


class RiskLevel(StrEnum):
    """Risk levels for predictions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PredictionRequest(BaseModel):
    """Request for match prediction."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    competition_id: int | None = None
    force_refresh: bool = False
    markets: list[PredictionMarket] | None = None  # None = all markets


class ProbabilityDistribution(BaseModel):
    """Normalized probability distribution for a market."""

    market: PredictionMarket
    outcomes: dict[str, float] = Field(default_factory=dict)
    total: float = Field(default=1.0, ge=0.99, le=1.01)

    @property
    def primary_outcome(self) -> tuple[str, float]:
        """Return the outcome with highest probability."""
        if not self.outcomes:
            return ("unknown", 0.0)
        best = max(self.outcomes, key=self.outcomes.get)  # type: ignore[arg-type]
        return (best, self.outcomes[best])


class ConsensusResult(BaseModel):
    """Aggregated consensus from multiple signals."""

    source_count: int = 0
    agreement_score: float = Field(default=0.0, ge=0, le=1)
    weighted_probability: ProbabilityDistribution | None = None
    signal_strength: float = Field(default=0.0, ge=0, le=1)
    factors: list[str] = Field(default_factory=list)


class PredictionRiskAssessment(BaseModel):
    """Risk assessment for a prediction."""

    level: RiskLevel = RiskLevel.MEDIUM
    score: float = Field(default=0.5, ge=0, le=1)
    volatility: float = Field(default=0.0, ge=0, le=1)
    data_completeness: float = Field(default=1.0, ge=0, le=1)
    provider_reliability: float = Field(default=1.0, ge=0, le=1)
    stability: float = Field(default=0.5, ge=0, le=1)
    factors: list[str] = Field(default_factory=list)


class KellyResult(BaseModel):
    """Kelly criterion calculation result."""

    fraction: float = Field(default=0.0, ge=0, le=1)
    edge: float = Field(default=0.0)
    expected_value: float = Field(default=0.0)
    recommended: bool = False


class ValueBet(BaseModel):
    """Value bet recommendation."""

    market: PredictionMarket
    outcome: str
    model_probability: float = Field(ge=0, le=1)
    market_odds: float = Field(gt=1.0)
    implied_probability: float = Field(ge=0, le=1)
    edge: float = Field(default=0.0)
    expected_value: float = Field(default=0.0)
    kelly: KellyResult = Field(default_factory=KellyResult)
    explanation: str = ""


class PredictionExplanation(BaseModel):
    """Human-readable explanation of a prediction."""

    summary: str
    key_factors: list[str] = Field(default_factory=list)
    home_advantages: list[str] = Field(default_factory=list)
    away_advantages: list[str] = Field(default_factory=list)
    market_insights: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MarketPrediction(BaseModel):
    """Prediction for a single market."""

    market: PredictionMarket
    distribution: ProbabilityDistribution
    confidence: float = Field(default=0.5, ge=0, le=1)
    risk: PredictionRiskAssessment = Field(default_factory=PredictionRiskAssessment)
    value_bets: list[ValueBet] = Field(default_factory=list)
    explanation: PredictionExplanation | None = None


class PredictionResult(BaseModel):
    """Full prediction result for a fixture."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    predictions: list[MarketPrediction] = Field(default_factory=list)
    consensus: ConsensusResult = Field(default_factory=ConsensusResult)
    overall_confidence: float = Field(default=0.5, ge=0, le=1)
    overall_risk: PredictionRiskAssessment = Field(
        default_factory=PredictionRiskAssessment
    )
    explanation: PredictionExplanation | None = None
    model_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    prediction_time_ms: float = 0.0
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PredictionSummary(BaseModel):
    """Lightweight summary of a prediction."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    home_win_pct: float = 0.0
    draw_pct: float = 0.0
    away_win_pct: float = 0.0
    confidence: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    top_value_bet: ValueBet | None = None
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PredictionHistory(BaseModel):
    """Stored prediction for historical tracking."""

    id: int | None = None
    fixture_id: int
    prediction: PredictionResult
    actual_outcome: str | None = None
    is_correct: bool | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
