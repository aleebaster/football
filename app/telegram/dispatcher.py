"""Telegram bot dispatcher configuration."""

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.telegram.handlers.callbacks import callback_handler
from app.telegram.handlers.start import start_command


def setup_dispatcher(application: Application) -> Application:  # type: ignore[type-arg]  # type: ignore[type-arg]
    """Setup all handlers on the application."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CallbackQueryHandler(callback_handler))
    return application
