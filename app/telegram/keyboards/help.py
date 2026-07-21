"""Help keyboard."""

from app.telegram.callbacks import HelpCallback, MenuCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_help_menu_keyboard() -> object:
    """Get help submenu keyboard."""
    return create_inline_keyboard(
        [
            [
                ("📖 Гід", HelpCallback.GUIDE.value),
                ("❓ FAQ", HelpCallback.FAQ.value),
            ],
            [
                ("📞 Контакти", HelpCallback.CONTACT.value),
            ],
            [
                ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
                ("🏠 Головне меню", MenuCallback.HOME.value),
            ],
        ]
    )
