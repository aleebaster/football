"""API Routers package — all API routers."""

from app.api.routers.backtesting import router as backtesting_router
from app.api.routers.configuration import router as configuration_router
from app.api.routers.health import router as health_router
from app.api.routers.live import router as live_router
from app.api.routers.live_dashboard import router as live_dashboard_router
from app.api.routers.matches import router as matches_router
from app.api.routers.predictions import router as predictions_router
from app.api.routers.providers import router as providers_router
from app.api.routers.signals import router as signals_router
from app.api.routers.statistics import router as statistics_router

__all__ = [
    "backtesting_router",
    "configuration_router",
    "health_router",
    "live_router",
    "live_dashboard_router",
    "matches_router",
    "predictions_router",
    "providers_router",
    "signals_router",
    "statistics_router",
]
