"""AI analysis keyboard."""

from app.telegram.callbacks import AICallback, MenuCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_ai_menu_keyboard() -> object:
    """Get AI analysis submenu keyboard."""
    return create_inline_keyboard(
        [
            [
                ("🔬 Аналіз матчу", AICallback.ANALYSIS.value),
                ("🎯 Прогнози", AICallback.PREDICTIONS.value),
            ],
            [
                ("📊 Патерни", AICallback.PATTERNS.value),
            ],
            [
                ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
                ("🏠 Головне меню", MenuCallback.HOME.value),
            ],
        ]
    )
