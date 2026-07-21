"""Monitoring menu keyboard."""

from app.telegram.callbacks import MenuCallback, MonitoringCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_monitoring_menu_keyboard():
    """Get monitoring submenu keyboard."""
    return create_inline_keyboard(
        [
            [
                ("➕ Додати турнір", MonitoringCallback.ADD.value),
                ("➖ Видалити", MonitoringCallback.REMOVE.value),
            ],
            [
                ("📋 Список", MonitoringCallback.LIST.value),
                ("🔄 Автооновлення", MonitoringCallback.AUTO_UPDATE.value),
            ],
            [
                ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
                ("🏠 Головне меню", MenuCallback.HOME.value),
            ],
        ]
    )
