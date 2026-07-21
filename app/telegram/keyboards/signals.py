"""Signals menu keyboard."""

from app.telegram.callbacks import MenuCallback, SignalsCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_signals_menu_keyboard() -> object:
    """Get signals submenu keyboard."""
    return create_inline_keyboard([
        [
            ("🟢 Активні", SignalsCallback.ACTIVE.value),
            ("📋 Історія", SignalsCallback.HISTORY.value),
        ],
        [
            ("⭐ Улюблені", SignalsCallback.FAVORITES.value),
            ("⚙️ Налаштування", SignalsCallback.SETTINGS.value),
        ],
        [
            ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
            ("🏠 Головне меню", MenuCallback.HOME.value),
        ],
    ])
