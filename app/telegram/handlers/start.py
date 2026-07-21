"""Start command handler."""

from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.keyboards.main_menu import get_main_menu_keyboard
from app.telegram.keyboards.reply import get_main_reply_keyboard
from app.telegram.messages import WELCOME_TEXT


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message:
        await update.message.reply_text(
            text=WELCOME_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=get_main_reply_keyboard(),
        )
        await update.message.reply_text(
            text="Виберіть розділ:",
            reply_markup=get_main_menu_keyboard(),
        )
