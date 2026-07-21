"""Start command handler."""

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.telegram.keyboards.main_menu import get_main_menu_keyboard
from app.telegram.keyboards.reply import get_main_reply_keyboard
from app.telegram.messages import WELCOME_TEXT


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is not None:
        reply_keyboard: ReplyKeyboardMarkup = get_main_reply_keyboard()
        await update.message.reply_text(
            text=WELCOME_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=reply_keyboard,
        )
        inline_keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            text="Виберіть розділ:",
            reply_markup=inline_keyboard,  # type: ignore[arg-type]
        )
