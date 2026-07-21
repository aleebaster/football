"""Top opportunities keyboard."""

from app.telegram.callbacks import MenuCallback, TopCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_top_menu_keyboard() -> object:
    """Get top opportunities submenu keyboard."""
    return create_inline_keyboard(
        [
            [
                ("💰 ТОП EV", TopCallback.EV.value),
                ("🏆 ТОП турнірів", TopCallback.TOURNAMENTS.value),
            ],
            [
                ("⚽ ТОП команд", TopCallback.TEAMS.value),
            ],
            [
                ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
                ("🏠 Головне меню", MenuCallback.HOME.value),
            ],
        ]
    )
