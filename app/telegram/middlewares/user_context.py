"""User context middleware for Telegram bot.

Provides user context to handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.middlewares.base import BaseMiddleware

logger = get_logger(__name__)


class UserContextMiddleware(BaseMiddleware):
    """Middleware for providing user context."""

    async def pre_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Inject user context into bot data."""
        if update.effective_user:
            context.bot_data["current_user_id"] = update.effective_user.id
            context.bot_data["current_username"] = update.effective_user.username
            context.bot_data["current_language"] = update.effective_user.language_code

        if update.effective_chat:
            context.bot_data["current_chat_id"] = update.effective_chat.id

    async def post_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Clean up user context."""
        context.bot_data.pop("current_user_id", None)
        context.bot_data.pop("current_username", None)
        context.bot_data.pop("current_language", None)
        context.bot_data.pop("current_chat_id", None)
