"""Error handling middleware for Telegram bot.

Catches and logs all exceptions with traceback.
"""

import traceback

from telegram import Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.factories import MessageFactory
from app.telegram.middlewares.base import BaseMiddleware

logger = get_logger(__name__)


class ErrorMiddleware(BaseMiddleware):
    """Middleware for handling errors gracefully."""

    async def pre_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Pre-process hook (no-op for error middleware)."""

    async def post_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Post-process hook (no-op for error middleware)."""

    def on_error(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception,
    ) -> None:
        """Handle errors with logging and user notification.

        Args:
            update: Telegram update.
            context: Bot context.
            error: The exception that was raised.
        """
        # Log full traceback
        tb_str = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        logger.error(f"Error occurred: {error}\nTraceback:\n{tb_str}")

        # Notify user asynchronously
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            try:
                error_text = MessageFactory.error_message(
                    "Сталася помилка. Спробуйте ще раз."
                )
                if update.callback_query:
                    import asyncio

                    asyncio.create_task(
                        update.callback_query.answer(text="⚠️ Помилка", show_alert=True)
                    )
                elif update.message:
                    import asyncio

                    asyncio.create_task(
                        update.message.reply_text(
                            text=error_text, parse_mode="MarkdownV2"
                        )
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
