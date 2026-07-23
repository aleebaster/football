"""Match DTO — match data for API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class MatchDTO(BaseModel):
    """Match data for API response."""

    fixture_id: int
    home_team_id: int | None = None
    home_team: str = ""
    home_team_crest: str | None = None
    away_team_id: int | None = None
    away_team: str = ""
    away_team_crest: str | None = None
    competition_id: int | None = None
    competition_name: str | None = None
    status: str = "SCHEDULED"
    utc_date: datetime | None = None
    home_score: int | None = None
    away_score: int | None = None
    venue: str | None = None


class MatchListDTO(BaseModel):
    """Paginated list of matches."""

    matches: list[MatchDTO] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)
