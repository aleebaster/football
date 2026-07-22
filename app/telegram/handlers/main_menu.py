"""Main menu handlers for Telegram bot.

Implements all 8 main menu sections.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.callbacks import (
    AICallback,
    HelpCallback,
    MarketCallback,
    MenuCallback,
    SettingsCallback,
    SignalsCallback,
    StatsCallback,
)
from app.telegram.factories import MessageFactory
from app.telegram.keyboards.factory import KeyboardFactory

logger = get_logger(__name__)


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu display."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = MessageFactory.main_menu()
    keyboard = KeyboardFactory.create_inline_keyboard(
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

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit main menu: {e}")


async def matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle matches section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""⚽ *МАТЧІ*

━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 *Пошук* — Знайти матч
📋 *Розклад* — Майбутні матчі
📊 *Результати* — Минулі матчі

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Оберіть опцію_ 👇"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit matches: {e}")


async def predictions_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle predictions section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""📈 *ПРОГНОЗИ*

━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 *AI Прогнози* — Штучний інтелект
🎯 *Точність* — Статистика прогнозів
📊 *Історія* — Минулі прогнози

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Оберіть опцію_ 👇"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit predictions: {e}")


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle statistics section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""📊 *СТАТИСТИКА*

━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 *Загальна* — Ваша статистика
📋 *Детальна* — Поглиблений аналіз
💾 *Експорт* — Завантажити дані

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Ваші результати та досягнення_ 👇"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit stats: {e}")


async def live_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle live section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""🔥 *LIVE*

━━━━━━━━━━━━━━━━━━━━━━━━━━

⚽ *Матчі наживо* — Поточні ігри
📊 *Статистика* — Live дані
📈 *Котирування* — Зміни ставок

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Слідкуйте за матчами наживо_ 👇"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit live: {e}")


async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle news section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""📰 *НОВИНИ*

━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 *Трансфери* — Останні новини
⚽ *Матчі* — Результати та аналіз
📊 *Ринок* — Зміни котирувань

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Останні новини світу футболу_ 👇"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit news: {e}")


async def favorites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle favorites section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""⭐ *ОБРАНЕ*

━━━━━━━━━━━━━━━━━━━━━━━━━━

⚽ *Матчі* — Збережені матчі
📈 *Прогнози* — Улюблені прогнози
🏆 *Турніри* — Обрані турніри

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Ваші збережені матеріали_ 👇"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit favorites: {e}")


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""⚙️ *НАЛАШТУВАННЯ*

━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 *Мова* — Обрати мову
🔔 *Сповіщення* — Налаштування
⏰ *Частота* — Частота оновлень
🎨 *Тема* — Оформлення

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Налаштуйте платформу під себе_ 👇"""

    keyboard = KeyboardFactory.create_inline_keyboard(
        [
            [("🌐 Мова", SettingsCallback.LANGUAGE.value)],
            [("🔔 Сповіщення", SettingsCallback.NOTIFICATIONS.value)],
            [("⏰ Частота", SettingsCallback.FREQUENCY.value)],
            [("🎨 Тема", SettingsCallback.THEME.value)],
            [
                ("⬅️ Назад", MenuCallback.BACK.value),
                ("🏠 Головне меню", MenuCallback.MAIN.value),
            ],
        ]
    )

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit settings: {e}")


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle about section."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    text = r"""ℹ️ *ПРО БОТА*

━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 *Football Analytics Platform*
📊 *Версія:* 1\.0\.0

⚡ *AI аналіз футбольних матчів*
📈 *Прогнози та сигнали*
📊 *Статистика та моніторинг*

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Створено з ❤️ для футбольних фанатів_"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    try:
        await query.edit_message_text(
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Failed to edit about: {e}")
