"""Telegram bot dispatcher configuration."""

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.telegram.handlers.callbacks import callback_handler
from app.telegram.handlers.start import start_command


def setup_dispatcher(app: Application) -> Application:
    """Setup all handlers on the application.

    Args:
        app: Telegram Application instance.

    Returns:
        Configured Application instance.
    """
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))

    # Callback query handler (main menu navigation)
    app.add_handler(CallbackQueryHandler(callback_handler))

    return app
