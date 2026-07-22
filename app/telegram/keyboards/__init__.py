"""Telegram keyboards package.

Provides centralized keyboard creation through KeyboardFactory.
"""

from app.telegram.keyboards.factory import (
    KeyboardFactory,
    create_inline_keyboard,
)

__all__ = [
    "KeyboardFactory",
    "create_inline_keyboard",
]
