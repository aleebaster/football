"""Backtesting Service — provides backtest data."""

from app.application.dto.backtest_dto import BacktestDTO, BacktestSummaryDTO
from app.application.mapper import Mapper
from app.backtesting.models import BacktestRequest, BacktestScope
from app.core.container import get_container


class BacktestingService:
    """Provides backtest data through the Backtesting Engine."""

    async def run_backtest(
        self,
        fixture_id: int | None = None,
        league_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        max_matches: int = 100,
    ) -> BacktestDTO:
        container = get_container()
        engine = container.backtest_engine

        if fixture_id is not None:
            scope = BacktestScope.SINGLE_MATCH
        elif league_id is not None:
            scope = BacktestScope.LEAGUE
        elif date_from is not None and date_to is not None:
            scope = BacktestScope.DATE_RANGE
        else:
            scope = BacktestScope.SINGLE_MATCH

        request = BacktestRequest(
            scope=scope,
            fixture_id=fixture_id,
            league_id=league_id,
            date_from=date_from,
            date_to=date_to,
            max_matches=max_matches,
        )

        try:
            result = await engine.run(request)
            return Mapper.to_backtest_dto(result)
        except Exception as e:
            return BacktestDTO(error=str(e))

    async def get_backtest(self, backtest_id: str) -> BacktestDTO | None:
        container = get_container()
        persistence = container.backtest_engine.persistence

        try:
            result = await persistence.get(backtest_id)
            if result is None:
                return None
            return Mapper.to_backtest_dto(result)
        except Exception:
            return None

    async def get_backtests(
        self,
        limit: int = 20,
    ) -> list[BacktestSummaryDTO]:
        container = get_container()
        persistence = container.backtest_engine.persistence

        try:
            results = await persistence.get_all()
            return [Mapper.to_backtest_summary_dto(r) for r in results[:limit]]
        except Exception:
            return []
