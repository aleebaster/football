"""Main menu keyboard."""

from app.telegram.callbacks import (
    AICallback,
    HelpCallback,
    MarketCallback,
    MonitoringCallback,
    SettingsCallback,
    SignalsCallback,
    StatsCallback,
    TopCallback,
)
from app.telegram.keyboards.factory import create_inline_keyboard


def get_main_menu_keyboard() -> object:
    """Get main menu inline keyboard with 2 buttons per row."""
    return create_inline_keyboard([
        [
            ("📊 Сигнали", SignalsCallback.ACTIVE.value),
            ("🔍 Пошук турніру", "tournament:search"),
        ],
        [
            ("👀 Моніторинг", MonitoringCallback.LIST.value),
            ("📈 Ринок", MarketCallback.LIVE_ODDS.value),
        ],
        [
            ("🏆 Турніри", "tournament:list"),
            ("⭐ ТОП можливостей", TopCallback.EV.value),
        ],
        [
            ("🧠 AI Аналіз", AICallback.ANALYSIS.value),
            ("📊 Статистика", StatsCallback.OVERVIEW.value),
        ],
        [
            ("⚙️ Налаштування", SettingsCallback.LANGUAGE.value),
            ("ℹ️ Допомога", HelpCallback.GUIDE.value),
        ],
    ])


def get_back_home_keyboard() -> object:
    """Get back and home buttons."""
    return create_inline_keyboard([
        [
            ("⬅️ Назад", "menu:back"),
            ("🏠 Головне меню", "menu:main"),
        ],
    ])
