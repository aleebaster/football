"""Timing middleware for Telegram bot.

Measures execution time of handlers.
"""

import time

from telegram import Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.middlewares.base import BaseMiddleware

logger = get_logger(__name__)


class TimingMiddleware(BaseMiddleware):
    """Middleware for measuring handler execution time."""

    def __init__(self) -> None:
        """Initialize timing middleware."""
        self._start_times: dict[int, float] = {}

    async def pre_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Record start time."""
        update_id = update.update_id
        self._start_times[update_id] = time.perf_counter()

    async def post_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Calculate and log execution time."""
        update_id = update.update_id
        start_time = self._start_times.pop(update_id, None)

        if start_time is not None:
            execution_time = time.perf_counter() - start_time
            user_id = update.effective_user.id if update.effective_user else "unknown"

            if execution_time > 1.0:  # Log slow handlers
                logger.warning(
                    f"Slow handler execution: {execution_time:.3f}s for user {user_id}"
                )
            else:
                logger.debug(
                    f"Handler executed in {execution_time:.3f}s for user {user_id}"
                )
