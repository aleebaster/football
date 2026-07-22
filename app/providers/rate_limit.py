"""Rate limiting utilities for providers.

Implements Token Bucket rate limiter for controlling API request rates.
"""

import asyncio
import time

from app.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter.

    Controls the rate of API requests to prevent exceeding rate limits.
    Uses asyncio lock for thread-safe token acquisition.
    """

    def __init__(self, rate: float = 10.0, burst: int = 20) -> None:
        """Initialize the rate limiter.

        Args:
            rate: Tokens per second refill rate.
            burst: Maximum token capacity.
        """
        self._rate = rate
        self._burst = burst
        self._tokens: float = float(burst)
        self._last_refill: float = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary.

        If no tokens available, waits until a token is refilled.
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_refill
            self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
            self._last_refill = now

            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self._rate
                logger.debug(f"Rate limited, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1

    def get_status(self) -> dict[str, float]:
        """Get current rate limiter status.

        Returns:
            Dictionary with tokens, rate, and burst values.
        """
        return {
            "tokens": self._tokens,
            "rate": self._rate,
            "burst": self._burst,
        }
