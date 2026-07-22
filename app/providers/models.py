"""Normalized Pydantic models for football data.

All provider responses are converted to these models.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProviderStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Competition(BaseModel):
    id: int
    name: str
    code: str | None = None
    country: str | None = None
    country_code: str | None = None
    emblem: str | None = None
    current_season: int | None = None
    current_matchday: int | None = None
    area: str | None = None
    plan: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class Season(BaseModel):
    id: int
    competition_id: int
    start_date: str | None = None
    end_date: str | None = None
    current_matchday: int | None = None
    winner: str | None = None


class Team(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    tla: str | None = None
    country: str | None = None
    founded: int | None = None
    venue: str | None = None
    club_colors: str | None = None
    crest: str | None = None
    coach: str | None = None
    coach_nationality: str | None = None
    league_position: int | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class Venue(BaseModel):
    id: int | None = None
    name: str | None = None
    address: str | None = None
    city: str | None = None
    capacity: int | None = None
    surface: str | None = None
    image: str | None = None


class Coach(BaseModel):
    id: int | None = None
    name: str | None = None
    nationality: str | None = None
    date_of_birth: str | None = None
    contract: str | None = None


class Player(BaseModel):
    id: int
    name: str
    first_name: str | None = None
    last_name: str | None = None
    nationality: str | None = None
    position: str | None = None
    date_of_birth: str | None = None
    age: int | None = None
    market_value: int | None = None
    jersey_number: int | None = None
    shirt_number: int | None = None
    height: float | None = None
    weight: float | None = None
    team_id: int | None = None


class FixtureStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    TIMED = "TIMED"
    IN_PLAY = "IN_PLAY"
    PAUSED = "PAUSED"
    HALFTIME = "HALFTIME"
    FINISHED = "FINISHED"
    SUSPENDED = "SUSPENDED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"
    AWARDED = "AWARDED"
    TBD = "TBD"


class Fixture(BaseModel):
    id: int
    competition_id: int | None = None
    competition_name: str | None = None
    season_id: int | None = None
    matchday: int | None = None
    stage: str | None = None
    group: str | None = None
    status: str = FixtureStatus.SCHEDULED.value
    utc_date: datetime | None = None
    home_team_id: int | None = None
    home_team: str | None = None
    home_team_crest: str | None = None
    away_team_id: int | None = None
    away_team: str | None = None
    away_team_crest: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    half_time_home: int | None = None
    half_time_away: int | None = None
    referee: str | None = None
    venue: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class Standing(BaseModel):
    position: int
    team_id: int
    team: str
    team_crest: str | None = None
    played: int = 0
    won: int = 0
    draw: int = 0
    lost: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    form: str | None = None
    group: str | None = None


class Statistic(BaseModel):
    fixture_id: int
    team_id: int
    team: str | None = None
    statistics: dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    id: int | None = None
    fixture_id: int
    team_id: int | None = None
    team: str | None = None
    player: str | None = None
    player_id: int | None = None
    assist: str | None = None
    type: str | None = None
    detail: str | None = None
    comments: str | None = None
    elapsed: int | None = None
    extra_time: int | None = None


class OddsOutcome(BaseModel):
    name: str
    value: float
    handicap: float | None = None


class OddsMarket(BaseModel):
    name: str
    outcomes: list[OddsOutcome] = Field(default_factory=list)


class Odds(BaseModel):
    fixture_id: int
    bookmaker: str | None = None
    markets: list[OddsMarket] = Field(default_factory=list)
    last_updated: datetime | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class PredictionInput(BaseModel):
    fixture_id: int
    home_team_id: int
    away_team_id: int
    home_form: list[str] = Field(default_factory=list)
    away_form: list[str] = Field(default_factory=list)
    head_to_head: list[dict[str, Any]] = Field(default_factory=list)
    home_stats: dict[str, Any] = Field(default_factory=dict)
    away_stats: dict[str, Any] = Field(default_factory=dict)
    odds: Odds | None = None
