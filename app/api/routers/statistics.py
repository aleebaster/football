"""Statistics Router — statistics endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_statistics_service
from app.application.dto.statistics_dto import (
    LeagueStatisticsDTO,
    MarketStatisticsDTO,
    OverallStatisticsDTO,
    TeamStatisticsDTO,
)
from app.application.services.statistics_service import StatisticsService

router = APIRouter()


@router.get("/statistics", response_model=OverallStatisticsDTO)
async def get_statistics(
    service: StatisticsService = Depends(get_statistics_service),
) -> OverallStatisticsDTO:
    """Get overall system statistics."""
    return await service.get_overall_statistics()


@router.get("/statistics/roi", response_model=OverallStatisticsDTO)
async def get_statistics_roi(
    service: StatisticsService = Depends(get_statistics_service),
) -> OverallStatisticsDTO:
    """Get ROI statistics."""
    return await service.get_overall_statistics()


@router.get("/statistics/yield", response_model=OverallStatisticsDTO)
async def get_statistics_yield(
    service: StatisticsService = Depends(get_statistics_service),
) -> OverallStatisticsDTO:
    """Get yield statistics."""
    return await service.get_overall_statistics()


@router.get("/statistics/winrate", response_model=OverallStatisticsDTO)
async def get_statistics_winrate(
    service: StatisticsService = Depends(get_statistics_service),
) -> OverallStatisticsDTO:
    """Get win rate statistics."""
    return await service.get_overall_statistics()


@router.get("/statistics/markets", response_model=list[MarketStatisticsDTO])
async def get_statistics_by_market(
    service: StatisticsService = Depends(get_statistics_service),
) -> list[MarketStatisticsDTO]:
    """Get statistics broken down by market type."""
    return await service.get_statistics_by_market()


@router.get("/statistics/leagues", response_model=list[LeagueStatisticsDTO])
async def get_statistics_by_league(
    service: StatisticsService = Depends(get_statistics_service),
) -> list[LeagueStatisticsDTO]:
    """Get statistics broken down by league."""
    return await service.get_statistics_by_league()


@router.get("/statistics/teams", response_model=list[TeamStatisticsDTO])
async def get_statistics_by_team(
    service: StatisticsService = Depends(get_statistics_service),
) -> list[TeamStatisticsDTO]:
    """Get statistics broken down by team."""
    return await service.get_statistics_by_team()
