"""API Schemas — shared request/response models for the REST API."""

from pydantic import BaseModel, Field


class BacktestRunRequest(BaseModel):
    """Request body for running a backtest."""

    fixture_id: int | None = None
    league_id: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    max_matches: int = Field(default=100, ge=1, le=10000)


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    code: str | None = None


class MessageResponse(BaseModel):
    """Standard message response."""

    message: str
    success: bool = True
