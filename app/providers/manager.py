"""Provider manager with fallback, failover, priority, and health-based routing."""

import time
from typing import Any

from app.logging import get_logger
from app.providers.base import BaseProvider
from app.providers.cache import ProviderCache
from app.providers.exceptions import AllProvidersFailedError
from app.providers.models import (
    Competition,
    Fixture,
    Odds,
    ProviderStatus,
    Standing,
    Team,
)
from app.providers.registry import ProviderRegistry

logger = get_logger(__name__)


class ProviderManager:
    """Manages providers with fallback, failover, and health-based routing.

    Lifecycle: Call start() on application startup and stop() on shutdown
    to ensure HTTP clients are properly opened/closed.
    """

    def __init__(self, registry: ProviderRegistry, cache: ProviderCache) -> None:
        self._registry = registry
        self._cache = cache
        self._started = False
        self._degraded = False
        self._degraded_reason: str | None = None

    async def start(self) -> None:
        """Start all registered providers (open HTTP clients)."""
        if self._started:
            return
        self._degraded = False
        self._degraded_reason = None
        failed: list[str] = []
        for provider in self._registry.get_all():
            if hasattr(provider, "start"):
                try:
                    await provider.start()
                    logger.info(f"Started provider: {provider.name}")
                except Exception as e:
                    logger.error(f"Failed to start provider {provider.name}: {e}")
                    failed.append(f"{provider.name}: {e}")
        self._started = True
        if failed:
            self._degraded = True
            self._degraded_reason = f"Failed to start: {'; '.join(failed)}"
            logger.warning(
                f"ProviderManager started in DEGRADED MODE: {self._degraded_reason}"
            )
        else:
            logger.info(f"ProviderManager started ({len(self._registry)} providers)")

    async def stop(self) -> None:
        """Stop all registered providers (close HTTP clients)."""
        if not self._started:
            return
        for provider in self._registry.get_all():
            if hasattr(provider, "stop"):
                try:
                    await provider.stop()
                    logger.info(f"Stopped provider: {provider.name}")
                except Exception as e:
                    logger.error(f"Failed to stop provider {provider.name}: {e}")
        self._started = False
        self._degraded = False
        self._degraded_reason = None
        logger.info("ProviderManager stopped")

    def _get_active_providers(self) -> list[BaseProvider]:
        providers = self._registry.get_enabled()
        healthy = [
            p for p in providers if p.health_info.status != ProviderStatus.UNHEALTHY
        ]
        if healthy:
            return healthy
        return providers

    async def _execute_with_fallback(
        self, method: str, *args: Any, **kwargs: Any
    ) -> Any:
        providers = self._get_active_providers()
        errors: list[Exception] = []

        for provider in providers:
            try:
                func = getattr(provider, method)
                start = time.perf_counter()
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                provider.health_info.record_success(elapsed)
                logger.debug(
                    f"Provider {provider.name} succeeded for {method} ({elapsed:.3f}s)"
                )
                return result
            except Exception as e:
                provider.health_info.record_failure()
                errors.append(e)
                logger.warning(f"Provider {provider.name} failed for {method}: {e}")

        raise AllProvidersFailedError(
            f"All providers failed for {method}", errors=errors
        )

    async def _execute_with_cache(
        self, method: str, data_type: str, cache_key: str, *args: Any, **kwargs: Any
    ) -> Any:
        for provider in self._get_active_providers():
            cached = await self._cache.get(provider.name, data_type, cache_key)
            if cached is not None:
                return cached

        result = await self._execute_with_fallback(method, *args, **kwargs)

        if result is not None:
            for provider in self._get_active_providers():
                try:
                    await self._cache.set(provider.name, data_type, cache_key, result)
                except Exception:
                    pass

        return result

    async def competitions(self) -> list[Competition]:
        result = await self._execute_with_fallback("competitions")
        return list(result)

    async def teams(self, competition_id: int) -> list[Team]:
        result = await self._execute_with_fallback("teams", competition_id)
        return list(result)

    async def standings(
        self, competition_id: int, season: int | None = None
    ) -> list[Standing]:
        cache_key = f"{competition_id}:{season or 'current'}"
        result = await self._execute_with_cache(
            "standings", "standings", cache_key, competition_id, season
        )
        return list(result)

    async def fixtures(
        self,
        competition_id: int | None = None,
        team_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Fixture]:
        cache_key = f"{competition_id}:{team_id}:{date_from}:{date_to}:{status}:{limit}"
        result = await self._execute_with_cache(
            "fixtures",
            "fixtures",
            cache_key,
            competition_id,
            team_id,
            date_from,
            date_to,
            status,
            limit,
        )
        return list(result)

    async def fixture(self, fixture_id: int) -> Fixture | None:
        result = await self._execute_with_cache(
            "fixture", "fixture_detail", str(fixture_id), fixture_id
        )
        return result  # type: ignore[no-any-return]

    async def live(self) -> list[Fixture]:
        result = await self._execute_with_fallback("live")
        return list(result)

    async def events(self, fixture_id: int) -> list[dict[str, Any]]:
        result = await self._execute_with_fallback("events", fixture_id)
        return list(result)

    async def statistics(self, fixture_id: int) -> list[dict[str, Any]]:
        result = await self._execute_with_fallback("statistics", fixture_id)
        return list(result)

    async def odds(self, fixture_id: int) -> Odds | None:
        result = await self._execute_with_fallback("odds", fixture_id)
        return result  # type: ignore[no-any-return]

    async def head_to_head(
        self, team_a_id: int, team_b_id: int, limit: int = 10
    ) -> list[Fixture]:
        cache_key = f"{team_a_id}:{team_b_id}:{limit}"
        result = await self._execute_with_cache(
            "head_to_head",
            "head_to_head",
            cache_key,
            team_a_id,
            team_b_id,
            limit,
        )
        return list(result)

    async def search(self, query: str) -> list[dict[str, Any]]:
        result = await self._execute_with_fallback("search", query)
        return list(result)

    @property
    def degraded(self) -> bool:
        """Check if the manager is running in degraded mode."""
        return self._degraded

    @property
    def degraded_reason(self) -> str | None:
        """Get the reason for degraded mode."""
        return self._degraded_reason

    def get_health_report(self) -> dict[str, Any]:
        providers = self._registry.get_all()
        return {
            "total": len(providers),
            "enabled": len([p for p in providers if p.enabled]),
            "healthy": len(
                [p for p in providers if p.health_info.status == ProviderStatus.HEALTHY]
            ),
            "degraded": self._degraded,
            "degraded_reason": self._degraded_reason,
            "providers": {p.name: p.health_info.to_dict() for p in providers},
        }
