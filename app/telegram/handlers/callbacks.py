"""Main callback handler dispatcher.

Uses new MessageFactory, KeyboardFactory, and NavigationManager.
"""

from collections.abc import Callable

from telegram import InlineKeyboardMarkup, Message, Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.callbacks import (
    AICallback,
    CallbackDataFactory,
    HelpCallback,
    MarketCallback,
    MenuCallback,
    MonitoringCallback,
    SettingsCallback,
    SignalsCallback,
    StatsCallback,
    TopCallback,
    TournamentCallback,
)
from app.telegram.factories import MessageFactory
from app.telegram.keyboards.factory import KeyboardFactory
from app.telegram.navigation import navigation

logger = get_logger(__name__)

# Mapping of callback data to (message_text, keyboard_factory)
MENU_HANDLERS: dict[str, tuple[str, Callable[[], InlineKeyboardMarkup]]] = {
    MenuCallback.MAIN.value: (
        MessageFactory.main_menu(),
        KeyboardFactory.create_back_home_keyboard,
    ),
    SignalsCallback.ACTIVE.value: (
        MessageFactory.loading("Сигнали"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    SignalsCallback.HISTORY.value: (
        MessageFactory.loading("Історія"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    SignalsCallback.FAVORITES.value: (
        MessageFactory.loading("Обране"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MonitoringCallback.ADD.value: (
        MessageFactory.loading("Моніторинг"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MonitoringCallback.REMOVE.value: (
        MessageFactory.loading("Моніторинг"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MonitoringCallback.LIST.value: (
        MessageFactory.loading("Список моніторингу"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MonitoringCallback.AUTO.value: (
        MessageFactory.loading("Автооновлення"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MarketCallback.LIVE_ODDS.value: (
        MessageFactory.loading("Котирування"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MarketCallback.MOVERS.value: (
        MessageFactory.loading("Ринок"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MarketCallback.TRENDING.value: (
        MessageFactory.loading("Тренд"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    MarketCallback.CHANGES.value: (
        MessageFactory.loading("Зміни"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    TopCallback.EV.value: (
        MessageFactory.loading("ТОП EV"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    TopCallback.TOURNAMENTS.value: (
        MessageFactory.loading("Турніри"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    TopCallback.TEAMS.value: (
        MessageFactory.loading("Команди"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    AICallback.ANALYSIS.value: (
        MessageFactory.loading("AI Аналіз"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    AICallback.PREDICTIONS.value: (
        MessageFactory.loading("Прогнози"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    AICallback.PATTERNS.value: (
        MessageFactory.loading("Патерни"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    StatsCallback.OVERVIEW.value: (
        MessageFactory.loading("Статистика"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    StatsCallback.DETAILED.value: (
        MessageFactory.loading("Детальна статистика"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    StatsCallback.EXPORT.value: (
        MessageFactory.loading("Експорт"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    SettingsCallback.LANGUAGE.value: (
        MessageFactory.loading("Налаштування"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    SettingsCallback.NOTIFICATIONS.value: (
        MessageFactory.loading("Сповіщення"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    SettingsCallback.FREQUENCY.value: (
        MessageFactory.loading("Частота"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    SettingsCallback.THEME.value: (
        MessageFactory.loading("Тема"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    HelpCallback.GUIDE.value: (
        MessageFactory.loading("Допомога"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    HelpCallback.FAQ.value: (
        MessageFactory.loading("FAQ"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    HelpCallback.CONTACT.value: (
        MessageFactory.loading("Контакти"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    HelpCallback.ABOUT.value: (
        MessageFactory.loading("Про бота"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    TournamentCallback.SEARCH.value: (
        MessageFactory.loading("Турніри"),
        KeyboardFactory.create_back_home_keyboard,
    ),
    TournamentCallback.LIST.value: (
        MessageFactory.loading("Список турнірів"),
        KeyboardFactory.create_back_home_keyboard,
    ),
}


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries using new factories."""
    query = update.callback_query
    if query is None or query.data is None:
        return

    await query.answer()

    user_id: int = query.from_user.id if query.from_user else 0
    callback_data: str = query.data
    text: str = MessageFactory.main_menu()
    keyboard: Callable[[], InlineKeyboardMarkup] = (
        KeyboardFactory.create_back_home_keyboard
    )

    # Validate callback data
    if not CallbackDataFactory.validate(callback_data):
        logger.warning(f"Invalid callback data: {callback_data}")
        return

    # Handle navigation callbacks
    if callback_data == MenuCallback.BACK.value:
        back_data, _ = await navigation.go_back(user_id)
        if back_data in MENU_HANDLERS:
            text, keyboard = MENU_HANDLERS[back_data]
    elif callback_data in (MenuCallback.MAIN.value, MenuCallback.HOME.value):
        await navigation.go_home(user_id)
        text = MessageFactory.main_menu()

        def _main_menu_kb() -> InlineKeyboardMarkup:
            return KeyboardFactory.create_inline_keyboard(
                [
                    [
                        ("⚽ Матчі", SignalsCallback.ACTIVE.value),
                        ("📈 Прогнози", AICallback.PREDICTIONS.value),
                    ],
                    [
                        ("📊 Статистика", StatsCallback.OVERVIEW.value),
                        ("🔥 Live", MarketCallback.LIVE_ODDS.value),
                    ],
                    [
                        ("📰 Новини", HelpCallback.GUIDE.value),
                        ("⭐ Обране", SignalsCallback.FAVORITES.value),
                    ],
                    [
                        ("⚙️ Налаштування", SettingsCallback.LANGUAGE.value),
                        ("ℹ️ Про бота", HelpCallback.ABOUT.value),
                    ],
                ]
            )

        keyboard = _main_menu_kb
    else:
        await navigation.navigate(user_id, callback_data)
        if callback_data in MENU_HANDLERS:
            text, keyboard = MENU_HANDLERS[callback_data]

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard(),
        )
    except Exception as e:
        logger.error(f"Failed to edit message for user {user_id}: {e}")
        msg = query.message
        if isinstance(msg, Message):
            try:
                await msg.reply_text(
                    text=text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard(),
                )
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
