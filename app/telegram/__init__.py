"""Telegram bot package.

Production-ready Telegram platform for football analytics.
"""

from app.telegram.bot import TelegramBot
from app.telegram.callbacks import (
    AICallback,
    CallbackDataFactory,
    HelpCallback,
    MarketCallback,
    MenuCallback,
    MonitoringCallback,
    SettingsCallback,
    SignalsCallback,
    StatsCallback,
    TopCallback,
    TournamentCallback,
)
from app.telegram.factories import MessageFactory
from app.telegram.localization import localization
from app.telegram.markdown import escape_markdown_v2
from app.telegram.navigation import NavigationManager, navigation
from app.telegram.router import Router, router
from app.telegram.state import State, StateManager, state_manager

__all__ = [
    "TelegramBot",
    "CallbackDataFactory",
    "MessageFactory",
    "NavigationManager",
    "Router",
    "StateManager",
    "State",
    "escape_markdown_v2",
    "localization",
    "navigation",
    "router",
    "state_manager",
    # Callback enums
    "MenuCallback",
    "SignalsCallback",
    "MonitoringCallback",
    "MarketCallback",
    "TopCallback",
    "AICallback",
    "StatsCallback",
    "SettingsCallback",
    "HelpCallback",
    "TournamentCallback",
]
