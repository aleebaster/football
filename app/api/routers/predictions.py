"""Predictions Router — prediction endpoints."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_prediction_service
from app.application.dto.prediction_dto import PredictionDTO, PredictionSummaryDTO
from app.application.services.prediction_service import PredictionService

router = APIRouter()


@router.get("/predictions/{fixture_id}", response_model=PredictionDTO)
async def get_prediction(
    fixture_id: int,
    home_team_id: int = Query(0, description="Home team ID"),
    away_team_id: int = Query(0, description="Away team ID"),
    home_team: str = Query("", description="Home team name"),
    away_team: str = Query("", description="Away team name"),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictionDTO:
    """Get full prediction for a match."""
    return await service.get_prediction(
        fixture_id=fixture_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_team=home_team,
        away_team=away_team,
    )


@router.get(
    "/predictions/{fixture_id}/summary",
    response_model=PredictionSummaryDTO,
)
async def get_prediction_summary(
    fixture_id: int,
    home_team_id: int = Query(0),
    away_team_id: int = Query(0),
    home_team: str = Query(""),
    away_team: str = Query(""),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictionSummaryDTO:
    """Get lightweight prediction summary for a match."""
    return await service.get_prediction_summary(
        fixture_id=fixture_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_team=home_team,
        away_team=away_team,
    )
