"""Telegram handlers package."""

from app.telegram.handlers.callbacks import callback_handler
from app.telegram.handlers.main_menu import (
    about_handler,
    favorites_handler,
    live_handler,
    main_menu_handler,
    matches_handler,
    news_handler,
    predictions_handler,
    settings_handler,
    stats_handler,
)
from app.telegram.handlers.start import help_command, start_command

__all__ = [
    "start_command",
    "help_command",
    "callback_handler",
    "main_menu_handler",
    "matches_handler",
    "predictions_handler",
    "stats_handler",
    "live_handler",
    "news_handler",
    "favorites_handler",
    "settings_handler",
    "about_handler",
]
