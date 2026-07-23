"""Statistics Service — provides statistics data."""

from app.application.dto.statistics_dto import (
    LeagueStatisticsDTO,
    MarketStatisticsDTO,
    OverallStatisticsDTO,
    TeamStatisticsDTO,
)
from app.application.mapper import Mapper
from app.backtesting.models import EvaluationResult
from app.core.container import get_container


class StatisticsService:
    """Provides statistics data from backtesting results."""

    async def get_overall_statistics(self) -> OverallStatisticsDTO:
        container = get_container()
        persistence = container.backtest_engine.persistence

        try:
            results = await persistence.get_all()
            if not results:
                return OverallStatisticsDTO()

            all_evaluations: list[EvaluationResult] = []
            for r in results:
                all_evaluations.extend(r.evaluations)

            if not all_evaluations:
                return OverallStatisticsDTO()

            metrics_calc = container.backtest_engine.metrics
            metrics = await metrics_calc.calculate(all_evaluations)
            return Mapper.to_overall_statistics_dto(metrics)
        except Exception:
            return OverallStatisticsDTO()

    async def get_statistics_by_market(self) -> list[MarketStatisticsDTO]:
        container = get_container()
        persistence = container.backtest_engine.persistence

        try:
            results = await persistence.get_all()
            all_evaluations: list[EvaluationResult] = []
            for r in results:
                all_evaluations.extend(r.evaluations)

            if not all_evaluations:
                return []

            metrics_calc = container.backtest_engine.metrics
            breakdowns = metrics_calc.calculate_market_breakdown(all_evaluations)
            return Mapper.to_market_statistics_dtos(list(breakdowns))
        except Exception:
            return []

    async def get_statistics_by_league(
        self,
        league_map: dict[int, str] | None = None,
    ) -> list[LeagueStatisticsDTO]:
        container = get_container()
        persistence = container.backtest_engine.persistence

        try:
            results = await persistence.get_all()
            all_evaluations: list[EvaluationResult] = []
            for r in results:
                all_evaluations.extend(r.evaluations)

            if not all_evaluations:
                return []

            stats = container.backtest_engine.statistics
            league_stats = stats.calculate_by_league(all_evaluations, league_map)
            return Mapper.to_league_statistics_dtos(league_stats)
        except Exception:
            return []

    async def get_statistics_by_team(self) -> list[TeamStatisticsDTO]:
        """Get statistics broken down by team."""
        return []
