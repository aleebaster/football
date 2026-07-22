"""Abstract BaseProvider defining the unified data provider contract.

All football data providers must implement this interface.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from app.logging import get_logger
from app.providers.models import (
    Competition,
    Fixture,
    Odds,
    ProviderStatus,
    Standing,
    Team,
)

logger = get_logger(__name__)


class ProviderHealth:
    """Health status tracking for a provider."""

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_response_time: float = 0.0
        self.last_success: datetime | None = None
        self.last_failure: datetime | None = None
        self.last_sync: datetime | None = None
        self.consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def average_response_time(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests

    @property
    def status(self) -> ProviderStatus:
        if self.total_requests == 0:
            return ProviderStatus.UNKNOWN
        if self.consecutive_failures >= 5:
            return ProviderStatus.UNHEALTHY
        if self.success_rate >= 95:
            return ProviderStatus.HEALTHY
        if self.success_rate >= 70:
            return ProviderStatus.DEGRADED
        return ProviderStatus.UNHEALTHY

    def record_success(self, response_time: float) -> None:
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time += response_time
        self.last_success = datetime.now(UTC)
        self.last_sync = datetime.now(UTC)
        self.consecutive_failures = 0

    def record_failure(self) -> None:
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure = datetime.now(UTC)
        self.consecutive_failures += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 2),
            "average_response_time": round(self.average_response_time, 4),
            "last_success": self.last_success.isoformat()
            if self.last_success
            else None,
            "last_failure": self.last_failure.isoformat()
            if self.last_failure
            else None,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "consecutive_failures": self.consecutive_failures,
        }


class BaseProvider(ABC):
    """Abstract base class for all football data providers."""

    def __init__(self, name: str, api_key: str = "", priority: int = 0) -> None:
        self._name = name
        self._api_key = api_key
        self._priority = priority
        self._health = ProviderHealth()
        self._enabled = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def health_info(self) -> ProviderHealth:
        return self._health

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @abstractmethod
    async def check_health(self) -> ProviderStatus:
        """Check provider health status."""
        ...

    @abstractmethod
    async def competitions(self) -> list[Competition]: ...

    @abstractmethod
    async def teams(self, competition_id: int) -> list[Team]: ...

    @abstractmethod
    async def standings(
        self, competition_id: int, season: int | None = None
    ) -> list[Standing]: ...

    @abstractmethod
    async def fixtures(
        self,
        competition_id: int | None = None,
        team_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Fixture]: ...

    @abstractmethod
    async def fixture(self, fixture_id: int) -> Fixture | None: ...

    @abstractmethod
    async def live(self) -> list[Fixture]: ...

    @abstractmethod
    async def events(self, fixture_id: int) -> list[Any]: ...

    @abstractmethod
    async def statistics(self, fixture_id: int) -> list[Any]: ...

    @abstractmethod
    async def odds(self, fixture_id: int) -> Odds | None: ...

    @abstractmethod
    async def head_to_head(
        self, team_a_id: int, team_b_id: int, limit: int = 10
    ) -> list[Fixture]: ...

    @abstractmethod
    async def search(self, query: str) -> list[Any]: ...

    async def last_update(self) -> datetime | None:
        return self._health.last_sync

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self._name}', priority={self._priority})>"
