"""API Dependencies — FastAPI dependency injection for API layer."""

from fastapi import Request

from app.application.services.backtesting_service import BacktestingService
from app.application.services.configuration_service import ConfigurationService
from app.application.services.health_service import HealthService
from app.application.services.live_service import LiveService
from app.application.services.match_service import MatchService
from app.application.services.prediction_service import PredictionService
from app.application.services.provider_service import ProviderService
from app.application.services.signal_service import SignalService
from app.application.services.statistics_service import StatisticsService


def get_health_service() -> HealthService:
    """Get health service instance."""
    return HealthService()


def get_match_service() -> MatchService:
    """Get match service instance."""
    return MatchService()


def get_prediction_service() -> PredictionService:
    """Get prediction service instance."""
    return PredictionService()


def get_signal_service() -> SignalService:
    """Get signal service instance."""
    return SignalService()


def get_backtesting_service() -> BacktestingService:
    """Get backtesting service instance."""
    return BacktestingService()


def get_statistics_service() -> StatisticsService:
    """Get statistics service instance."""
    return StatisticsService()


def get_provider_service() -> ProviderService:
    """Get provider service instance."""
    return ProviderService()


def get_configuration_service() -> ConfigurationService:
    """Get configuration service instance."""
    return ConfigurationService()


def get_live_service() -> LiveService:
    """Get live service instance."""
    return LiveService()


def get_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID from request."""
    return request.headers.get("X-Request-ID", "")


def get_page_params(
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, int]:
    """Extract pagination parameters."""
    return (max(1, page), min(100, max(1, page_size)))
