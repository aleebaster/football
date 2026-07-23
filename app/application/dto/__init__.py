"""Data Transfer Objects — lightweight representations for API responses."""

from app.application.dto.backtest_dto import BacktestDTO, BacktestSummaryDTO
from app.application.dto.configuration_dto import ConfigurationDTO
from app.application.dto.health_dto import HealthDTO, ProviderHealthDTO
from app.application.dto.match_dto import MatchDTO, MatchListDTO
from app.application.dto.prediction_dto import PredictionDTO, PredictionSummaryDTO
from app.application.dto.provider_dto import ProviderDTO, ProviderListDTO
from app.application.dto.signal_dto import SignalDTO, SignalListDTO
from app.application.dto.statistics_dto import (
    LeagueStatisticsDTO,
    MarketStatisticsDTO,
    OverallStatisticsDTO,
    TeamStatisticsDTO,
)

__all__ = [
    "BacktestDTO",
    "BacktestSummaryDTO",
    "ConfigurationDTO",
    "HealthDTO",
    "LeagueStatisticsDTO",
    "MarketStatisticsDTO",
    "MatchDTO",
    "MatchListDTO",
    "OverallStatisticsDTO",
    "PredictionDTO",
    "PredictionSummaryDTO",
    "ProviderDTO",
    "ProviderHealthDTO",
    "ProviderListDTO",
    "SignalDTO",
    "SignalListDTO",
    "TeamStatisticsDTO",
]
