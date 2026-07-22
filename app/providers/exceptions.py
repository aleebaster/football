"""Custom exceptions for the data provider platform."""


class ProviderError(Exception):
    """Base exception for all provider errors."""

    def __init__(
        self, message: str, provider: str = "", cause: Exception | None = None
    ) -> None:
        self.provider = provider
        self.cause = cause
        super().__init__(message)


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not registered."""


class ProviderHealthError(ProviderError):
    """Raised when a provider fails health check."""


class RateLimitError(ProviderError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float = 0,
        provider: str = "",
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, provider=provider)


class CircuitBreakerOpenError(ProviderError):
    """Raised when circuit breaker is open."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class AllProvidersFailedError(ProviderError):
    """Raised when all providers in the chain have failed."""

    def __init__(
        self,
        message: str = "All providers failed",
        errors: list[Exception] | None = None,
        provider: str = "",
    ) -> None:
        self.errors = errors or []
        super().__init__(message, provider=provider)


class DataNormalizationError(ProviderError):
    """Raised when data normalization fails."""
