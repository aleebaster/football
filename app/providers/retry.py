"""Retry and circuit breaker utilities for providers.

Implements Circuit Breaker pattern for fault tolerance.
"""

import time

from app.logging import get_logger

logger = get_logger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance.

    States:
        - closed: Normal operation, requests allowed
        - open: Too many failures, requests blocked
        - half-open: Testing if service recovered
    """

    def __init__(
        self, failure_threshold: int = 5, recovery_timeout: float = 60.0
    ) -> None:
        """Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit.
            recovery_timeout: Seconds to wait before trying again.
        """
        self._failure_count: int = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float = 0.0
        self._state: str = "closed"  # closed, open, half-open

    @property
    def state(self) -> str:
        """Get current circuit breaker state.

        Automatically transitions from open to half-open after recovery timeout.
        """
        if self._state == "open":
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = "half-open"
        return self._state

    def record_success(self) -> None:
        """Record a successful request. Resets failure count and closes circuit."""
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        """Record a failed request. Opens circuit if threshold exceeded."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = "open"
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )

    def allow_request(self) -> bool:
        """Check if a request is allowed.

        Returns:
            True if request is allowed (closed or half-open state).
        """
        state = self.state
        return state in ("closed", "half-open")
