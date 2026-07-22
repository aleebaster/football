"""Logging middleware for Telegram bot.

Logs all incoming commands, callbacks, and navigation.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.middlewares.base import BaseMiddleware

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging bot interactions."""

    async def pre_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log incoming update."""
        user_id = update.effective_user.id if update.effective_user else "unknown"
        username = (
            update.effective_user.username if update.effective_user else "unknown"
        )

        if update.message and update.message.text:
            text = update.message.text
            if text.startswith("/"):
                logger.info(
                    f"Command received: {text} from user {username} ({user_id})"
                )
            else:
                logger.debug(f"Message from {username} ({user_id}): {text[:50]}...")

        if update.callback_query:
            query = update.callback_query
            logger.info(
                f"Callback received: {query.data} from user {username} ({user_id})"
            )

    async def post_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Post-process hook."""
        pass
