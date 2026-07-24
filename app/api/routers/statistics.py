"""Statistics Router — statistics endpoints.

Note on /statistics/roi, /statistics/yield, /statistics/winrate:
These endpoints return the full OverallStatisticsDTO which contains all
metrics (win_rate, roi, yield_pct, etc.) in a single aggregated response.
They are kept as convenience aliases for frontend clients that expect
dedicated endpoints, but they share the same underlying computation to
avoid duplicating business logic. If you need only a specific metric,
extract it from the response payload.
"""

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
    """Get ROI statistics.

    Returns the full statistics payload including roi, win_rate, yield_pct, etc.
    This is a convenience alias — ROI can also be read from the /statistics endpoint.
    """
    return await service.get_overall_statistics()


@router.get("/statistics/yield", response_model=OverallStatisticsDTO)
async def get_statistics_yield(
    service: StatisticsService = Depends(get_statistics_service),
) -> OverallStatisticsDTO:
    """Get yield statistics.

    Returns the full statistics payload including yield_pct, roi, win_rate, etc.
    This is a convenience alias — yield can also be read from the /statistics endpoint.
    """
    return await service.get_overall_statistics()


@router.get("/statistics/winrate", response_model=OverallStatisticsDTO)
async def get_statistics_winrate(
    service: StatisticsService = Depends(get_statistics_service),
) -> OverallStatisticsDTO:
    """Get win rate statistics.

    Returns the full statistics payload including win_rate, roi, yield_pct, etc.
    This is a convenience alias — win rate can also be read from the /statistics endpoint.
    """
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
    """Get statistics broken down by team.

    Note: This endpoint is currently a placeholder that returns an empty list.
    Team-level aggregation requires mapping fixture team IDs to names from
    backtesting evaluation results, which is planned for a future iteration.
    """
    return await service.get_statistics_by_team()
