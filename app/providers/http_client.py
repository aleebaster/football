"""Centralized HTTP Client for provider API calls.

Features: httpx AsyncClient, timeout, retry, connection pool, HTTP/2, rate limiter, exponential backoff, circuit breaker.
"""

import asyncio
import time
from dataclasses import dataclass

import httpx

from app.logging import get_logger
from app.providers.exceptions import (
    CircuitBreakerOpenError,
    ProviderTimeoutError,
    RateLimitError,
)
from app.providers.rate_limit import RateLimiter
from app.providers.retry import CircuitBreaker

logger = get_logger(__name__)


@dataclass
class HttpClientConfig:
    """HTTP client configuration."""

    base_url: str = ""
    api_key: str = ""
    timeout: float = 30.0
    max_connections: int = 20
    max_keepalive: int = 10
    rate_limit: float = 10.0
    rate_burst: int = 20
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery: float = 60.0
    user_agent: str = "FootballAnalytics/1.0"


class HttpClient:
    """Centralized async HTTP client with resilience patterns."""

    def __init__(self, config: HttpClientConfig | None = None) -> None:
        self._config = config or HttpClientConfig()
        self._client: httpx.AsyncClient | None = None
        self._rate_limiter = RateLimiter(
            rate=self._config.rate_limit,
            burst=self._config.rate_burst,
        )
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self._config.circuit_breaker_threshold,
            recovery_timeout=self._config.circuit_breaker_recovery,
        )

    async def start(self) -> None:
        limits = httpx.Limits(
            max_connections=self._config.max_connections,
            max_keepalive_connections=self._config.max_keepalive,
        )
        # HTTP/2 requires the h2 package. Falls back to HTTP/1.1 if not installed.
        try:
            import h2  # noqa: F401

            http2 = True
        except ImportError:
            http2 = False
        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            timeout=httpx.Timeout(self._config.timeout),
            limits=limits,
            http2=http2,
            headers={
                "User-Agent": self._config.user_agent,
                "Accept": "application/json",
            },
        )
        logger.info(
            f"HTTP client started: {self._config.base_url} "
            f"(HTTP/{'2' if http2 else '1.1'})"
        )

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client stopped")

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("HTTP client not started. Call start() first.")
        return self._client

    async def request(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        if not self._circuit_breaker.allow_request():
            raise CircuitBreakerOpenError(
                "Circuit breaker is open", provider=self._config.base_url
            )

        await self._rate_limiter.acquire()

        request_headers = dict(headers) if headers else {}
        if self._config.api_key:
            request_headers["X-Api-Key"] = self._config.api_key

        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            start_time = time.perf_counter()
            try:
                response = await self.client.request(
                    method=method,
                    url=path,
                    headers=request_headers,
                    params=params,
                )
                elapsed = time.perf_counter() - start_time

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "5"))
                    self._circuit_breaker.record_failure()
                    raise RateLimitError(
                        retry_after=retry_after, provider=self._config.base_url
                    )

                response.raise_for_status()
                self._circuit_breaker.record_success()
                logger.debug(
                    f"HTTP {method} {path} -> {response.status_code} ({elapsed:.3f}s)"
                )
                return response

            except httpx.TimeoutException:
                elapsed = time.perf_counter() - start_time
                last_error = ProviderTimeoutError(
                    f"Timeout after {elapsed:.1f}s: {path}",
                    provider=self._config.base_url,
                )
                self._circuit_breaker.record_failure()
                logger.warning(f"Timeout on attempt {attempt + 1}: {path}")

            except httpx.HTTPStatusError as e:
                elapsed = time.perf_counter() - start_time
                if e.response.status_code >= 500:
                    last_error = e
                    self._circuit_breaker.record_failure()
                    logger.warning(
                        f"Server error {e.response.status_code} on attempt {attempt + 1}: {path}"
                    )
                else:
                    raise

            except RateLimitError:
                raise

            except Exception as e:
                last_error = e
                self._circuit_breaker.record_failure()
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")

            if attempt < self._config.max_retries - 1:
                delay = min(
                    self._config.retry_base_delay * (2**attempt),
                    self._config.retry_max_delay,
                )
                logger.debug(
                    f"Retrying in {delay:.1f}s (attempt {attempt + 2}/{self._config.max_retries})"
                )
                await asyncio.sleep(delay)

        raise last_error or ProviderTimeoutError(
            "All retries exhausted", provider=self._config.base_url
        )

    async def get(
        self, path: str, params: dict[str, str] | None = None
    ) -> httpx.Response:
        return await self.request("GET", path, params=params)

    async def post(
        self, path: str, params: dict[str, str] | None = None
    ) -> httpx.Response:
        return await self.request("POST", path, params=params)

    def get_health_info(self) -> dict[str, object]:
        return {
            "circuit_breaker_state": self._circuit_breaker.state,
            "rate_limiter": self._rate_limiter.get_status(),
        }
