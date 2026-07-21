"""Reply keyboard for main menu."""

from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu reply keyboard with large buttons."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📊 Сигнали"), KeyboardButton("🔍 Пошук")],
            [KeyboardButton("👀 Моніторинг"), KeyboardButton("📈 Ринок")],
            [KeyboardButton("🏆 Турніри"), KeyboardButton("⭐ ТОП")],
            [KeyboardButton("🧠 AI"), KeyboardButton("📊 Статистика")],
            [KeyboardButton("⚙️ Налаштування"), KeyboardButton("ℹ️ Допомога")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
