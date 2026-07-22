"""Data Provider Platform.

Provides unified interface for fetching football data from multiple sources.
"""

from app.providers.base import BaseProvider, ProviderHealth
from app.providers.cache import ProviderCache
from app.providers.exceptions import (
    AllProvidersFailedError,
    CircuitBreakerOpenError,
    DataNormalizationError,
    ProviderError,
    ProviderHealthError,
    ProviderNotFoundError,
    ProviderTimeoutError,
    RateLimitError,
)
from app.providers.health import HealthChecker
from app.providers.http_client import HttpClient, HttpClientConfig
from app.providers.manager import ProviderManager
from app.providers.rate_limit import RateLimiter
from app.providers.registry import ProviderRegistry
from app.providers.retry import CircuitBreaker
from app.providers.scheduler import ProviderScheduler

__all__ = [
    "BaseProvider",
    "ProviderHealth",
    "ProviderManager",
    "ProviderRegistry",
    "ProviderCache",
    "HealthChecker",
    "ProviderScheduler",
    "HttpClient",
    "HttpClientConfig",
    "CircuitBreaker",
    "RateLimiter",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderHealthError",
    "ProviderTimeoutError",
    "CircuitBreakerOpenError",
    "RateLimitError",
    "AllProvidersFailedError",
    "DataNormalizationError",
]
