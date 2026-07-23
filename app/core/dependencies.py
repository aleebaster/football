"""Composition Root — central dependency injection container.

All services are assembled here and shared across the application.
This module delegates to the Container for all dependency creation.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.engine import AIEngine
from app.backtesting.engine import BacktestEngine
from app.cache.base import CacheManager
from app.core.container import get_container
from app.database.session import db_manager
from app.prediction.engine import PredictionEngine
from app.providers.cache import ProviderCache
from app.providers.manager import ProviderManager
from app.providers.registry import ProviderRegistry
from app.signals.engine import SignalEngine


def get_cache_manager() -> CacheManager:
    """Get the global cache manager from the container."""
    return get_container().cache_manager


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    async for session in db_manager.get_session():
        yield session


def get_cache() -> CacheManager:
    """Dependency for getting cache manager."""
    return get_cache_manager()


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry from the container."""
    return get_container().provider_registry


def get_provider_cache() -> ProviderCache:
    """Get the provider cache from the container."""
    return get_container().provider_cache


def get_provider_manager() -> ProviderManager:
    """Get the global provider manager from the container."""
    return get_container().provider_manager


def get_ai_engine() -> AIEngine:
    """Get the global AI engine from the container."""
    return get_container().ai_engine


def get_prediction_engine() -> PredictionEngine:
    """Get the global Prediction Engine from the container."""
    return get_container().prediction_engine


def get_signal_engine() -> SignalEngine:
    """Get the global Signal Engine from the container."""
    return get_container().signal_engine


def get_backtesting_engine() -> BacktestEngine:
    """Get the global Backtesting Engine from the container."""
    return get_container().backtest_engine


def register_default_providers() -> None:
    """Register default providers based on configuration."""
    from app.config import settings
    from app.providers.adapters.mock_provider import MockProvider

    container = get_container()
    registry = container.provider_registry

    if len(registry) == 0:
        registry.register(MockProvider(priority=100))

    if settings.provider.api_football_key:
        from app.providers.adapters.api_football import ApiFootballProvider

        registry.register(
            ApiFootballProvider(
                api_key=settings.provider.api_football_key,
                priority=10,
            )
        )

    if settings.provider.football_data_key:
        from app.providers.adapters.football_data import FootballDataProvider

        registry.register(
            FootballDataProvider(
                api_key=settings.provider.football_data_key,
                priority=20,
            )
        )
