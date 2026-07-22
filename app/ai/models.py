"""Pydantic models for AI Analysis Engine."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MatchOutcome(StrEnum):
    HOME_WIN = "home_win"
    DRAW = "draw"
    AWAY_WIN = "away_win"


class AnalysisStatus(StrEnum):
    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILED = "failed"


class FeatureSource(BaseModel):
    """Source of a feature with confidence metadata."""

    analyzer: str
    data_completeness: float = Field(ge=0, le=1, default=1.0)
    freshness_seconds: float = Field(ge=0, default=0.0)


class FeatureVector(BaseModel):
    """Aggregated feature vector from all analyzers."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    features: dict[str, Any] = Field(default_factory=dict)
    sources: list[FeatureSource] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def get(self, key: str, default: Any = None) -> Any:
        return self.features.get(key, default)

    def set_feature(self, key: str, value: Any, source: FeatureSource) -> None:
        self.features[key] = value
        self.sources.append(source)


class RuleResult(BaseModel):
    """Result of a single rule evaluation."""

    rule_id: str
    name: str
    weight: float = Field(ge=0, le=1)
    impact: float = Field(ge=-1, le=1)
    outcome: MatchOutcome
    description: str
    explanation: str
    data_used: list[str] = Field(default_factory=list)


class ConfidenceResult(BaseModel):
    """Confidence assessment of the analysis."""

    overall: float = Field(ge=0, le=1)
    risk: float = Field(ge=0, le=1)
    stability: float = Field(ge=0, le=1)
    data_quality: float = Field(ge=0, le=1)
    provider_quality: float = Field(ge=0, le=1)
    factors: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Risk assessment for a prediction."""

    level: str  # low, medium, high, very_high
    score: float = Field(ge=0, le=1)
    factors: list[str] = Field(default_factory=list)
    mitigation: str = ""


class Explanation(BaseModel):
    """Human-readable explanation of the analysis."""

    summary: str
    key_factors: list[str] = Field(default_factory=list)
    home_advantages: list[str] = Field(default_factory=list)
    away_advantages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PredictionContext(BaseModel):
    """Context for prediction engine consumption."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    features: dict[str, Any] = Field(default_factory=dict)
    probability_home: float = Field(ge=0, le=1)
    probability_draw: float = Field(ge=0, le=1)
    probability_away: float = Field(ge=0, le=1)
    confidence: ConfidenceResult | None = None
    risk: RiskAssessment | None = None


class AnalysisRequest(BaseModel):
    """Request for match analysis."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    competition_id: int | None = None
    force_refresh: bool = False
    analyzers: list[str] | None = None  # None = all analyzers


class AnalysisContext(BaseModel):
    """Internal context passed between analyzers."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    competition_id: int | None = None
    fixture_data: Any = None
    home_standings: Any = None
    away_standings: Any = None
    home_fixtures: list[Any] = Field(default_factory=list)
    away_fixtures: list[Any] = Field(default_factory=list)
    head_to_head: list[Any] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
    odds: Any = None
    events: list[Any] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Final analysis result."""

    fixture_id: int
    home_team_id: int
    away_team_id: int
    status: AnalysisStatus
    prediction: PredictionContext | None = None
    features: FeatureVector | None = None
    rules: list[RuleResult] = Field(default_factory=list)
    confidence: ConfidenceResult | None = None
    risk: RiskAssessment | None = None
    explanation: Explanation | None = None
    analyzers_used: list[str] = Field(default_factory=list)
    analysis_time_ms: float = 0.0
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
