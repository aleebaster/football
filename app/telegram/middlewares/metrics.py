"""Metrics middleware for Telegram bot.

Collects metrics on bot usage.
"""

import time
from dataclasses import dataclass, field

from telegram import Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.middlewares.base import BaseMiddleware

logger = get_logger(__name__)


@dataclass
class BotMetrics:
    """Bot metrics container."""

    total_commands: int = 0
    total_callbacks: int = 0
    total_messages: int = 0
    total_errors: int = 0
    unique_users: set[int] = field(default_factory=set)
    command_counts: dict[str, int] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    @property
    def uptime(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self.start_time

    @property
    def total_users(self) -> int:
        """Get total unique users."""
        return len(self.unique_users)


class MetricsMiddleware(BaseMiddleware):
    """Middleware for collecting bot metrics."""

    def __init__(self) -> None:
        """Initialize metrics middleware."""
        self.metrics = BotMetrics()

    async def pre_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Collect metrics from incoming update."""
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            self.metrics.unique_users.add(user_id)

        if update.message and update.message.text:
            text = update.message.text
            if text.startswith("/"):
                self.metrics.total_commands += 1
                command = text.split()[0][1:]  # Remove /
                self.metrics.command_counts[command] = (
                    self.metrics.command_counts.get(command, 0) + 1
                )
            else:
                self.metrics.total_messages += 1

        if update.callback_query:
            self.metrics.total_callbacks += 1

    async def post_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Post-process hook."""
        pass

    def on_error(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception,
    ) -> None:
        """Count errors."""
        self.metrics.total_errors += 1

    def get_stats(self) -> dict[str, object]:
        """Get current metrics as dictionary.

        Returns:
            Dictionary with metrics.
        """
        return {
            "uptime_seconds": self.metrics.uptime,
            "total_commands": self.metrics.total_commands,
            "total_callbacks": self.metrics.total_callbacks,
            "total_messages": self.metrics.total_messages,
            "total_errors": self.metrics.total_errors,
            "total_users": self.metrics.total_users,
            "command_counts": dict(self.metrics.command_counts),
        }


# Global metrics instance
metrics = MetricsMiddleware()
