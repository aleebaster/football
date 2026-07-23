"""Dependency injection functions for FastAPI.

Provides injectable dependencies for services and utilities.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.base import CacheManager
from app.cache.memory import MemoryCache
from app.config import settings
from app.database.session import db_manager
from app.providers.cache import ProviderCache
from app.providers.manager import ProviderManager
from app.providers.registry import ProviderRegistry

# Global instances
_cache: CacheManager | None = None
_provider_registry: ProviderRegistry | None = None
_provider_manager: ProviderManager | None = None
_ai_engine: Any = None
_prediction_engine: Any = None
_signal_engine: Any = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager.

    Returns:
        CacheManager instance.
    """
    global _cache
    if _cache is None:
        backend = MemoryCache(
            max_size=settings.cache.max_size,
            default_ttl=settings.cache.ttl,
        )
        _cache = CacheManager(backend)
    return _cache


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions.

    Yields:
        AsyncSession: Database session.
    """
    async for session in db_manager.get_session():
        yield session


def get_cache() -> CacheManager:
    """Dependency for getting cache manager.

    Returns:
        CacheManager instance.
    """
    return get_cache_manager()


def get_provider_registry() -> ProviderRegistry:
    """Get or create the global provider registry.

    Returns:
        ProviderRegistry instance.
    """
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
    return _provider_registry


def get_provider_cache() -> ProviderCache:
    """Get or create the provider cache.

    Returns:
        ProviderCache instance.
    """
    return ProviderCache(get_cache_manager())


def get_provider_manager() -> ProviderManager:
    """Get or create the global provider manager.

    Returns:
        ProviderManager instance.
    """
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager(
            registry=get_provider_registry(),
            cache=get_provider_cache(),
        )
    return _provider_manager


def get_ai_engine() -> Any:
    """Get or create the global AI engine."""
    global _ai_engine
    if _ai_engine is None:
        from app.ai.engine import AIEngine

        _ai_engine = AIEngine(
            provider_manager=get_provider_manager(),
            cache_manager=get_cache_manager(),
        )
    return _ai_engine


def get_prediction_engine() -> Any:
    """Get or create the global Prediction Engine."""
    global _prediction_engine
    if _prediction_engine is None:
        from app.prediction.engine import PredictionEngine

        _prediction_engine = PredictionEngine(
            ai_engine=get_ai_engine(),
            cache_manager=get_cache_manager(),
        )
    return _prediction_engine


def get_signal_engine() -> Any:
    """Get or create the global Signal Engine.

    Creates all Signal Engine dependencies through the DI system.
    Returns:
        SignalEngine instance.
    """
    global _signal_engine
    if _signal_engine is None:
        from app.signals.cooldown import CooldownManager
        from app.signals.deduplication import DeduplicationManager
        from app.signals.engine import SignalEngine
        from app.signals.filtering import SignalFilter
        from app.signals.history import SignalHistoryStore
        from app.signals.metrics import MetricsCollector
        from app.signals.notifications import NotificationEngine
        from app.signals.persistence import SignalPersistence
        from app.signals.ranking import SignalRanker
        from app.signals.registry import SignalGeneratorRegistry
        from app.signals.scoring import SignalScorer
        from app.signals.validator import SignalValidator

        _signal_engine = SignalEngine(
            cache_manager=get_cache_manager(),
            registry=SignalGeneratorRegistry(),
            validator=SignalValidator(),
            signal_filter=SignalFilter(),
            deduplication=DeduplicationManager(),
            cooldown=CooldownManager(),
            scorer=SignalScorer(),
            ranker=SignalRanker(),
            notifications=NotificationEngine(),
            history=SignalHistoryStore(),
            persistence=SignalPersistence(),
            metrics=MetricsCollector(),
        )
    return _signal_engine


def register_default_providers() -> None:
    """Register default providers based on configuration."""
    registry = get_provider_registry()

    from app.providers.adapters.mock_provider import MockProvider

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
