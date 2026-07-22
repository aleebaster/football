"""Keyboard factory for creating Telegram keyboards.

Provides centralized creation of InlineKeyboard and ReplyKeyboard.
"""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.telegram.callbacks import MenuCallback


class KeyboardFactory:
    """Factory for creating all types of Telegram keyboards."""

    @staticmethod
    def create_inline_keyboard(
        rows: list[list[tuple[str, str]]],
    ) -> InlineKeyboardMarkup:
        """Create inline keyboard from rows of (text, callback_data) tuples.

        Args:
            rows: List of rows, each row is list of (text, callback_data) tuples.

        Returns:
            InlineKeyboardMarkup instance.
        """
        keyboard: list[list[InlineKeyboardButton]] = []
        for row in rows:
            buttons = [
                InlineKeyboardButton(text=text, callback_data=data)
                for text, data in row
            ]
            keyboard.append(buttons)
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_reply_keyboard(
        rows: list[list[str]],
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
    ) -> ReplyKeyboardMarkup:
        """Create reply keyboard from rows of button texts.

        Args:
            rows: List of rows, each row is list of button texts.
            resize_keyboard: Whether to resize keyboard.
            one_time_keyboard: Whether keyboard is one-time.

        Returns:
            ReplyKeyboardMarkup instance.
        """
        keyboard: list[list[KeyboardButton]] = []
        for row in rows:
            buttons = [KeyboardButton(text=text) for text in row]
            keyboard.append(buttons)
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard,
        )

    @staticmethod
    def create_pagination_keyboard(
        current_page: int,
        total_pages: int,
        callback_prefix: str,
    ) -> InlineKeyboardMarkup:
        """Create pagination keyboard.

        Args:
            current_page: Current page number (1-based).
            total_pages: Total number of pages.
            callback_prefix: Callback data prefix.

        Returns:
            InlineKeyboardMarkup with pagination buttons.
        """
        buttons: list[InlineKeyboardButton] = []

        if current_page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"{callback_prefix}:page:{current_page - 1}",
                )
            )

        buttons.append(
            InlineKeyboardButton(
                text=f"📄 {current_page}/{total_pages}",
                callback_data=f"{callback_prefix}:noop",
            )
        )

        if current_page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=f"{callback_prefix}:page:{current_page + 1}",
                )
            )

        return InlineKeyboardMarkup([buttons])

    @staticmethod
    def create_back_home_keyboard() -> InlineKeyboardMarkup:
        """Create navigation keyboard with Back and Home buttons.

        Returns:
            InlineKeyboardMarkup with navigation buttons.
        """
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=MenuCallback.BACK.value,
                    ),
                    InlineKeyboardButton(
                        text="🏠 Головне меню",
                        callback_data=MenuCallback.MAIN.value,
                    ),
                ],
            ]
        )

    @staticmethod
    def create_confirm_keyboard(
        confirm_text: str = "✅ Підтвердити",
        cancel_text: str = "❌ Скасувати",
        confirm_data: str = "confirm:yes",
        cancel_data: str = "confirm:no",
    ) -> InlineKeyboardMarkup:
        """Create confirmation keyboard.

        Args:
            confirm_text: Text for confirm button.
            cancel_text: Text for cancel button.
            confirm_data: Callback data for confirm.
            cancel_data: Callback data for cancel.

        Returns:
            InlineKeyboardMarkup with confirm/cancel buttons.
        """
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text=confirm_text, callback_data=confirm_data),
                    InlineKeyboardButton(text=cancel_text, callback_data=cancel_data),
                ],
            ]
        )

    @staticmethod
    def create_refresh_keyboard(
        refresh_data: str = "menu:refresh",
    ) -> InlineKeyboardMarkup:
        """Create refresh button keyboard.

        Args:
            refresh_data: Callback data for refresh button.

        Returns:
            InlineKeyboardMarkup with refresh button.
        """
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🔄 Оновити",
                        callback_data=refresh_data,
                    ),
                ],
            ]
        )


# Keep backward compatibility
def create_inline_keyboard(
    rows: list[list[tuple[str, str]]],
) -> InlineKeyboardMarkup:
    """Create inline keyboard (legacy function)."""
    return KeyboardFactory.create_inline_keyboard(rows)
