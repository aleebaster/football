"""Tests for KeyboardFactory."""

from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup

from app.telegram.keyboards.factory import KeyboardFactory, create_inline_keyboard


class TestKeyboardFactory:
    """Tests for KeyboardFactory."""

    def test_create_inline_keyboard(self) -> None:
        """Test inline keyboard creation."""
        rows = [
            [("Button 1", "data1"), ("Button 2", "data2")],
            [("Button 3", "data3")],
        ]
        keyboard = KeyboardFactory.create_inline_keyboard(rows)

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 2
        assert len(keyboard.inline_keyboard[0]) == 2
        assert len(keyboard.inline_keyboard[1]) == 1

    def test_create_reply_keyboard(self) -> None:
        """Test reply keyboard creation."""
        rows = [["Button 1", "Button 2"], ["Button 3"]]
        keyboard = KeyboardFactory.create_reply_keyboard(rows)

        assert isinstance(keyboard, ReplyKeyboardMarkup)
        assert len(keyboard.keyboard) == 2

    def test_create_pagination_keyboard(self) -> None:
        """Test pagination keyboard creation."""
        keyboard = KeyboardFactory.create_pagination_keyboard(
            current_page=2, total_pages=5, callback_prefix="list"
        )

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        # Should have back, page indicator, and forward buttons
        assert len(keyboard.inline_keyboard[0]) == 3

    def test_create_pagination_first_page(self) -> None:
        """Test pagination keyboard on first page."""
        keyboard = KeyboardFactory.create_pagination_keyboard(
            current_page=1, total_pages=5, callback_prefix="list"
        )

        # Should only have page indicator and forward buttons
        assert len(keyboard.inline_keyboard[0]) == 2

    def test_create_pagination_last_page(self) -> None:
        """Test pagination keyboard on last page."""
        keyboard = KeyboardFactory.create_pagination_keyboard(
            current_page=5, total_pages=5, callback_prefix="list"
        )

        # Should only have back and page indicator buttons
        assert len(keyboard.inline_keyboard[0]) == 2

    def test_create_back_home_keyboard(self) -> None:
        """Test back/home keyboard creation."""
        keyboard = KeyboardFactory.create_back_home_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 2

    def test_create_confirm_keyboard(self) -> None:
        """Test confirm keyboard creation."""
        keyboard = KeyboardFactory.create_confirm_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 2

    def test_create_refresh_keyboard(self) -> None:
        """Test refresh keyboard creation."""
        keyboard = KeyboardFactory.create_refresh_keyboard()

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 1

    def test_legacy_create_inline_keyboard(self) -> None:
        """Test legacy function still works."""
        rows = [[("Button", "data")]]
        keyboard = create_inline_keyboard(rows)

        assert isinstance(keyboard, InlineKeyboardMarkup)
