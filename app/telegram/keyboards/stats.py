"""Statistics keyboard."""

from app.telegram.callbacks import MenuCallback, StatsCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_stats_menu_keyboard():
    """Get statistics submenu keyboard."""
    return create_inline_keyboard(
        [
            [
                ("📈 Загальна", StatsCallback.OVERVIEW.value),
                ("📋 Детальна", StatsCallback.DETAILED.value),
            ],
            [
                ("💾 Експорт", StatsCallback.EXPORT.value),
            ],
            [
                ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
                ("🏠 Головне меню", MenuCallback.HOME.value),
            ],
        ]
    )
