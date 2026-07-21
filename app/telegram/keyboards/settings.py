"""Settings keyboard."""

from app.telegram.callbacks import MenuCallback, SettingsCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_settings_menu_keyboard() -> object:
    """Get settings submenu keyboard."""
    return create_inline_keyboard([
        [
            ("🌐 Мова", SettingsCallback.LANGUAGE.value),
            ("🔔 Повідомлення", SettingsCallback.NOTIFICATIONS.value),
        ],
        [
            ("⏰ Частота", SettingsCallback.FREQUENCY.value),
            ("🎨 Тема", SettingsCallback.THEME.value),
        ],
        [
            ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
            ("🏠 Головне меню", MenuCallback.HOME.value),
        ],
    ])
