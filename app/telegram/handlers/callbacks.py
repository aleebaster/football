"""Main callback handler dispatcher."""

from collections.abc import Callable
from typing import Any

from telegram import Message, Update
from telegram.ext import ContextTypes

from app.logging import get_logger
from app.telegram.keyboards.main_menu import (
    get_back_home_keyboard,
    get_main_menu_keyboard,
)
from app.telegram.messages import (
    AI_MENU_TEXT,
    HELP_CONTACT_TEXT,
    HELP_GUIDE_TEXT,
    MAIN_MENU_TEXT,
    MARKET_ODDS_TEXT,
    MONITORING_LIST_TEXT,
    SETTINGS_LANGUAGE_TEXT,
    SETTINGS_MENU_TEXT,
    SIGNALS_ACTIVE_TEXT,
    SIGNALS_HISTORY_TEXT,
    STATS_OVERVIEW_TEXT,
    TOP_EV_TEXT,
)
from app.telegram.navigation import navigation

logger = get_logger(__name__)

MENU_HANDLERS: dict[str, tuple[str, Callable[[], Any]]] = {
    "menu:main": (MAIN_MENU_TEXT, get_main_menu_keyboard),
    "signals:active": (SIGNALS_ACTIVE_TEXT, get_back_home_keyboard),
    "signals:history": (SIGNALS_HISTORY_TEXT, get_back_home_keyboard),
    "signals:favorites": (SIGNALS_HISTORY_TEXT, get_back_home_keyboard),
    "monitoring:add": (MONITORING_LIST_TEXT, get_back_home_keyboard),
    "monitoring:remove": (MONITORING_LIST_TEXT, get_back_home_keyboard),
    "monitoring:list": (MONITORING_LIST_TEXT, get_back_home_keyboard),
    "monitoring:auto": (MONITORING_LIST_TEXT, get_back_home_keyboard),
    "market:odds": (MARKET_ODDS_TEXT, get_back_home_keyboard),
    "market:movers": (MARKET_ODDS_TEXT, get_back_home_keyboard),
    "market:trending": (MARKET_ODDS_TEXT, get_back_home_keyboard),
    "market:changes": (MARKET_ODDS_TEXT, get_back_home_keyboard),
    "top:ev": (TOP_EV_TEXT, get_back_home_keyboard),
    "top:tournaments": (TOP_EV_TEXT, get_back_home_keyboard),
    "top:teams": (TOP_EV_TEXT, get_back_home_keyboard),
    "ai:analysis": (AI_MENU_TEXT, get_back_home_keyboard),
    "ai:predictions": (AI_MENU_TEXT, get_back_home_keyboard),
    "ai:patterns": (AI_MENU_TEXT, get_back_home_keyboard),
    "stats:overview": (STATS_OVERVIEW_TEXT, get_back_home_keyboard),
    "stats:detailed": (STATS_OVERVIEW_TEXT, get_back_home_keyboard),
    "stats:export": (STATS_OVERVIEW_TEXT, get_back_home_keyboard),
    "settings:language": (SETTINGS_LANGUAGE_TEXT, get_back_home_keyboard),
    "settings:notifications": (SETTINGS_MENU_TEXT, get_back_home_keyboard),
    "settings:frequency": (SETTINGS_MENU_TEXT, get_back_home_keyboard),
    "settings:theme": (SETTINGS_MENU_TEXT, get_back_home_keyboard),
    "help:guide": (HELP_GUIDE_TEXT, get_back_home_keyboard),
    "help:faq": (HELP_GUIDE_TEXT, get_back_home_keyboard),
    "help:contact": (HELP_CONTACT_TEXT, get_back_home_keyboard),
    "tournament:search": (MAIN_MENU_TEXT, get_main_menu_keyboard),
    "tournament:list": (MAIN_MENU_TEXT, get_main_menu_keyboard),
}


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries."""
    query = update.callback_query
    if query is None or query.data is None:
        return

    await query.answer()

    user_id: int = query.from_user.id if query.from_user else 0
    callback_data: str = query.data
    text: str = MAIN_MENU_TEXT
    keyboard: Callable[[], Any] = get_main_menu_keyboard

    if callback_data == "menu:back":
        back_data, _ = await navigation.go_back(user_id)
        if back_data in MENU_HANDLERS:
            text, keyboard = MENU_HANDLERS[back_data]
    elif callback_data == "menu:main":
        await navigation.go_home(user_id)
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
        msg: Message | None = query.message
        if isinstance(msg, Message):
            try:
                await msg.reply_text(
                    text=text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard(),
                )
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
