"""Tests for Application Layer — DTOs, Services, Mapper, Dashboard Presenter."""

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
from app.application.mapper import Mapper
from app.application.services.configuration_service import ConfigurationService
from app.application.services.health_service import HealthService

# ===== DTO Tests =====


class TestHealthDTO:
    def test_health_dto_defaults(self) -> None:
        dto = HealthDTO()
        assert dto.status == "healthy"
        assert dto.version == "0.1.0"

    def test_provider_health_dto(self) -> None:
        dto = ProviderHealthDTO(
            name="mock",
            status="healthy",
            success_rate=0.95,
        )
        assert dto.name == "mock"
        assert dto.status == "healthy"


class TestMatchDTO:
    def test_match_dto(self) -> None:
        dto = MatchDTO(fixture_id=123, home_team="Team A", away_team="Team B")
        assert dto.fixture_id == 123
        assert dto.home_team == "Team A"

    def test_match_list_dto(self) -> None:
        dto = MatchListDTO(matches=[], total=0)
        assert dto.total == 0
        assert dto.page == 1


class TestPredictionDTO:
    def test_prediction_dto(self) -> None:
        dto = PredictionDTO(fixture_id=100, overall_confidence=0.75)
        assert dto.fixture_id == 100
        assert dto.overall_confidence == 0.75

    def test_prediction_summary_dto(self) -> None:
        dto = PredictionSummaryDTO(
            fixture_id=100,
            home_win_pct=0.6,
            draw_pct=0.2,
            away_win_pct=0.2,
        )
        assert dto.fixture_id == 100
        assert dto.home_win_pct == 0.6


class TestSignalDTO:
    def test_signal_dto(self) -> None:
        dto = SignalDTO(id="sig-1", fixture_id=100, outcome="home")
        assert dto.id == "sig-1"
        assert dto.outcome == "home"

    def test_signal_list_dto(self) -> None:
        dto = SignalListDTO(signals=[], total=0, page=1, page_size=20)
        assert dto.total == 0


class TestBacktestDTO:
    def test_backtest_dto(self) -> None:
        dto = BacktestDTO(id="bt-1", scope="single_match", status="completed")
        assert dto.id == "bt-1"
        assert dto.status == "completed"

    def test_backtest_summary_dto(self) -> None:
        dto = BacktestSummaryDTO(win_rate=0.7, roi=0.15)
        assert dto.win_rate == 0.7
        assert dto.roi == 0.15


class TestProviderDTO:
    def test_provider_dto(self) -> None:
        dto = ProviderDTO(name="mock", status="healthy")
        assert dto.name == "mock"
        assert dto.status == "healthy"

    def test_provider_list_dto(self) -> None:
        dto = ProviderListDTO(total=3, healthy=2, degraded=1, unhealthy=0)
        assert dto.total == 3
        assert dto.healthy == 2


class TestStatisticsDTO:
    def test_overall_statistics_dto(self) -> None:
        dto = OverallStatisticsDTO(win_rate=0.65, roi=0.12)
        assert dto.win_rate == 0.65
        assert dto.roi == 0.12

    def test_league_statistics_dto(self) -> None:
        dto = LeagueStatisticsDTO(league_id=1, league_name="PL", win_rate=0.7)
        assert dto.league_name == "PL"

    def test_market_statistics_dto(self) -> None:
        dto = MarketStatisticsDTO(market="match_winner", win_rate=0.6)
        assert dto.market == "match_winner"

    def test_team_statistics_dto(self) -> None:
        dto = TeamStatisticsDTO(team_id=1, team_name="Arsenal", win_rate=0.8)
        assert dto.team_name == "Arsenal"


class TestConfigurationDTO:
    def test_configuration_dto(self) -> None:
        dto = ConfigurationDTO(project_name="Football Analysis", debug=False)
        assert dto.project_name == "Football Analysis"
        assert dto.debug is False


# ===== Mapper Tests =====


class TestMapper:
    def test_to_health_dto_empty(self) -> None:
        dto = Mapper.to_health_dto(providers=[])
        assert dto.status == "healthy"
        assert len(dto.providers) == 0
        assert len(dto.engines) == 4

    def test_to_health_dto_with_providers(self) -> None:
        providers = [
            {
                "name": "mock",
                "status": "healthy",
                "success_rate": 0.95,
                "avg_response_ms": 50.0,
                "consecutive_failures": 0,
            }
        ]
        dto = Mapper.to_health_dto(providers=providers)
        assert len(dto.providers) == 1
        assert dto.providers[0].name == "mock"

    def test_to_match_dto_from_fixture(self) -> None:
        from app.providers.models import Fixture

        fixture = Fixture(
            id=123,
            home_team="Team A",
            away_team="Team B",
            status="SCHEDULED",
        )
        dto = Mapper.to_match_dto(fixture)
        assert dto.fixture_id == 123
        assert dto.home_team == "Team A"
        assert dto.away_team == "Team B"

    def test_to_overall_statistics_dto(self) -> None:
        from app.backtesting.models import BacktestMetrics

        metrics = BacktestMetrics(
            total_predictions=100,
            win_rate=0.65,
            roi=0.12,
        )
        dto = Mapper.to_overall_statistics_dto(metrics)
        assert dto.total_predictions == 100
        assert dto.win_rate == 0.65

    def test_to_overall_statistics_dto_none(self) -> None:
        dto = Mapper.to_overall_statistics_dto(None)
        assert dto.total_predictions == 0


# ===== Service Tests =====


class TestHealthService:
    def test_get_health(self) -> None:
        service = HealthService()
        dto = service.get_health()
        assert dto.status == "healthy"
        assert dto.version == "0.1.0"


class TestConfigurationService:
    def test_get_configuration(self) -> None:
        service = ConfigurationService()
        dto = service.get_configuration()
        assert dto.project_name == "Football Analysis"
        assert isinstance(dto.version, str)
