"""Backtesting Router — backtest endpoints."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_backtesting_service
from app.api.schemas import BacktestRunRequest
from app.application.dto.backtest_dto import BacktestDTO, BacktestSummaryDTO
from app.application.services.backtesting_service import BacktestingService

router = APIRouter()


@router.post("/backtests", response_model=BacktestDTO)
async def run_backtest(
    request: BacktestRunRequest,
    service: BacktestingService = Depends(get_backtesting_service),
) -> BacktestDTO:
    """Run a new backtest."""
    return await service.run_backtest(
        fixture_id=request.fixture_id,
        league_id=request.league_id,
        date_from=request.date_from,
        date_to=request.date_to,
        max_matches=request.max_matches,
    )


@router.get("/backtests", response_model=list[BacktestSummaryDTO])
async def get_backtests(
    limit: int = Query(20, ge=1, le=100),
    service: BacktestingService = Depends(get_backtesting_service),
) -> list[BacktestSummaryDTO]:
    """Get list of recent backtests."""
    return await service.get_backtests(limit=limit)


@router.get("/backtests/{backtest_id}", response_model=BacktestDTO)
async def get_backtest(
    backtest_id: str,
    service: BacktestingService = Depends(get_backtesting_service),
) -> BacktestDTO:
    """Get a specific backtest by ID."""
    result = await service.get_backtest(backtest_id)
    if result is None:
        from app.api.exceptions import APINotFoundError

        raise APINotFoundError(f"Backtest {backtest_id} not found")
    return result
