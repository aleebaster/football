"""Callback data factory for Telegram bot menus."""

from enum import StrEnum


class MenuCallback(StrEnum):
    """Main menu callbacks."""
    MAIN_MENU = "menu:main"
    BACK = "menu:back"
    HOME = "menu:home"


class SignalsCallback(StrEnum):
    """Signals menu callbacks."""
    ACTIVE = "signals:active"
    HISTORY = "signals:history"
    FAVORITES = "signals:favorites"
    SETTINGS = "signals:settings"


class MonitoringCallback(StrEnum):
    """Monitoring menu callbacks."""
    ADD = "monitoring:add"
    REMOVE = "monitoring:remove"
    LIST = "monitoring:list"
    AUTO_UPDATE = "monitoring:auto"


class MarketCallback(StrEnum):
    """Market menu callbacks."""
    LIVE_ODDS = "market:odds"
    MOVERS = "market:movers"
    TRENDING = "market:trending"
    CHANGES = "market:changes"


class TopCallback(StrEnum):
    """Top opportunities callbacks."""
    EV = "top:ev"
    TOURNAMENTS = "top:tournaments"
    TEAMS = "top:teams"


class AICallback(StrEnum):
    """AI analysis callbacks."""
    ANALYSIS = "ai:analysis"
    PREDICTIONS = "ai:predictions"
    PATTERNS = "ai:patterns"


class StatsCallback(StrEnum):
    """Statistics callbacks."""
    OVERVIEW = "stats:overview"
    DETAILED = "stats:detailed"
    EXPORT = "stats:export"


class SettingsCallback(StrEnum):
    """Settings callbacks."""
    LANGUAGE = "settings:language"
    NOTIFICATIONS = "settings:notifications"
    FREQUENCY = "settings:frequency"
    THEME = "settings:theme"


class HelpCallback(StrEnum):
    """Help callbacks."""
    GUIDE = "help:guide"
    FAQ = "help:faq"
    CONTACT = "help:contact"
