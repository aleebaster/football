"""Matches Router — match data endpoints."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_match_service
from app.application.dto.match_dto import MatchDTO, MatchListDTO
from app.application.services.match_service import MatchService

router = APIRouter()


@router.get("/matches", response_model=MatchListDTO)
async def get_matches(
    competition_id: int | None = Query(None, description="Filter by competition ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of matches to return"),
    service: MatchService = Depends(get_match_service),
) -> MatchListDTO:
    """Get a list of matches.

    Optionally filter by competition ID and limit the number of results.
    """
    return await service.get_matches(competition_id=competition_id, limit=limit)


@router.get("/matches/{fixture_id}", response_model=MatchDTO)
async def get_match(
    fixture_id: int,
    service: MatchService = Depends(get_match_service),
) -> MatchDTO:
    """Get a specific match by fixture ID."""
    result = await service.get_match(fixture_id)
    if result is None:
        from app.api.exceptions import APINotFoundError

        raise APINotFoundError(f"Match {fixture_id} not found")
    return result
