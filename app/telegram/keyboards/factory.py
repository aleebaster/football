"""Keyboard factory for creating Telegram keyboards."""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def create_inline_keyboard(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """Create inline keyboard from rows of (text, callback_data) tuples.

    Args:
        rows: List of rows, each row is list of (text, callback_data) tuples.

    Returns:
        InlineKeyboardMarkup instance.
    """
    keyboard = []
    for row in rows:
        buttons = [InlineKeyboardButton(text=text, callback_data=data) for text, data in row]
        keyboard.append(buttons)
    return InlineKeyboardMarkup(keyboard)
