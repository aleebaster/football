"""Callback data factory for Telegram bot.

All callback_data should be generated through this factory.
No magic strings allowed.
"""

from enum import StrEnum


class CallbackCategory(StrEnum):
    """Callback categories."""

    MENU = "menu"
    SIGNALS = "signals"
    MONITORING = "monitoring"
    MARKET = "market"
    TOP = "top"
    AI = "ai"
    STATS = "stats"
    SETTINGS = "settings"
    HELP = "help"
    TOURNAMENT = "tournament"
    USER = "user"


class MenuCallback(StrEnum):
    """Menu navigation callbacks."""

    MAIN = "menu:main"
    BACK = "menu:back"
    HOME = "menu:home"
    REFRESH = "menu:refresh"


class SignalsCallback(StrEnum):
    """Signals section callbacks."""

    ACTIVE = "signals:active"
    HISTORY = "signals:history"
    FAVORITES = "signals:favorites"


class MonitoringCallback(StrEnum):
    """Monitoring section callbacks."""

    ADD = "monitoring:add"
    REMOVE = "monitoring:remove"
    LIST = "monitoring:list"
    AUTO = "monitoring:auto"


class MarketCallback(StrEnum):
    """Market section callbacks."""

    LIVE_ODDS = "market:odds"
    MOVERS = "market:movers"
    TRENDING = "market:trending"
    CHANGES = "market:changes"


class TopCallback(StrEnum):
    """Top section callbacks."""

    EV = "top:ev"
    TOURNAMENTS = "top:tournaments"
    TEAMS = "top:teams"


class AICallback(StrEnum):
    """AI section callbacks."""

    ANALYSIS = "ai:analysis"
    PREDICTIONS = "ai:predictions"
    PATTERNS = "ai:patterns"


class StatsCallback(StrEnum):
    """Statistics section callbacks."""

    OVERVIEW = "stats:overview"
    DETAILED = "stats:detailed"
    EXPORT = "stats:export"


class SettingsCallback(StrEnum):
    """Settings section callbacks."""

    LANGUAGE = "settings:language"
    NOTIFICATIONS = "settings:notifications"
    FREQUENCY = "settings:frequency"
    THEME = "settings:theme"


class HelpCallback(StrEnum):
    """Help section callbacks."""

    GUIDE = "help:guide"
    FAQ = "help:faq"
    CONTACT = "help:contact"
    ABOUT = "help:about"


class TournamentCallback(StrEnum):
    """Tournament section callbacks."""

    SEARCH = "tournament:search"
    LIST = "tournament:list"


class CallbackDataFactory:
    """Factory for creating and validating callback data."""

    @staticmethod
    def validate(callback_data: str) -> bool:
        """Validate callback data format.

        Args:
            callback_data: Callback data string to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not callback_data:
            return False

        parts = callback_data.split(":")
        if len(parts) < 2:
            return False

        category = parts[0]
        valid_categories = {
            c.value.split(":")[0] for c in CallbackCategory.__members__.values()
        }
        return category in valid_categories

    @staticmethod
    def create(category: str, action: str) -> str:
        """Create callback data string.

        Args:
            category: Callback category.
            action: Callback action.

        Returns:
            Formatted callback data string.
        """
        return f"{category}:{action}"

    @staticmethod
    def parse(callback_data: str) -> tuple[str, str]:
        """Parse callback data into category and action.

        Args:
            callback_data: Callback data string.

        Returns:
            Tuple of (category, action).
        """
        parts = callback_data.split(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], ""


# All callback handlers mapping
CALLBACK_HANDLERS: dict[str, str] = {
    MenuCallback.MAIN.value: "main_menu",
    MenuCallback.BACK.value: "go_back",
    MenuCallback.HOME.value: "go_home",
    MenuCallback.REFRESH.value: "refresh",
    SignalsCallback.ACTIVE.value: "signals_active",
    SignalsCallback.HISTORY.value: "signals_history",
    SignalsCallback.FAVORITES.value: "signals_favorites",
    MonitoringCallback.ADD.value: "monitoring_add",
    MonitoringCallback.REMOVE.value: "monitoring_remove",
    MonitoringCallback.LIST.value: "monitoring_list",
    MonitoringCallback.AUTO.value: "monitoring_auto",
    MarketCallback.LIVE_ODDS.value: "market_odds",
    MarketCallback.MOVERS.value: "market_movers",
    MarketCallback.TRENDING.value: "market_trending",
    MarketCallback.CHANGES.value: "market_changes",
    TopCallback.EV.value: "top_ev",
    TopCallback.TOURNAMENTS.value: "top_tournaments",
    TopCallback.TEAMS.value: "top_teams",
    AICallback.ANALYSIS.value: "ai_analysis",
    AICallback.PREDICTIONS.value: "ai_predictions",
    AICallback.PATTERNS.value: "ai_patterns",
    StatsCallback.OVERVIEW.value: "stats_overview",
    StatsCallback.DETAILED.value: "stats_detailed",
    StatsCallback.EXPORT.value: "stats_export",
    SettingsCallback.LANGUAGE.value: "settings_language",
    SettingsCallback.NOTIFICATIONS.value: "settings_notifications",
    SettingsCallback.FREQUENCY.value: "settings_frequency",
    SettingsCallback.THEME.value: "settings_theme",
    HelpCallback.GUIDE.value: "help_guide",
    HelpCallback.FAQ.value: "help_faq",
    HelpCallback.CONTACT.value: "help_contact",
    TournamentCallback.SEARCH.value: "tournament_search",
    TournamentCallback.LIST.value: "tournament_list",
}
