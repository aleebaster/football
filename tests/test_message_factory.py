"""Tests for MessageFactory."""

from app.telegram.factories import MessageFactory


class TestMessageFactory:
    """Tests for MessageFactory."""

    def test_escape_markdown(self) -> None:
        """Test markdown escaping."""
        text = "Hello *world*"
        escaped = MessageFactory.escape_markdown(text)
        assert "\\*" in escaped

    def test_bold_formatting(self) -> None:
        """Test bold formatting."""
        result = MessageFactory.bold("test")
        assert result == "*test*"

    def test_italic_formatting(self) -> None:
        """Test italic formatting."""
        result = MessageFactory.italic("test")
        assert result == "_test_"

    def test_code_formatting(self) -> None:
        """Test code formatting."""
        result = MessageFactory.code("test")
        assert result == "`test`"

    def test_link_formatting(self) -> None:
        """Test link formatting."""
        result = MessageFactory.link("click here", "https://example.com")
        assert "[click here](https://example.com)" in result

    def test_welcome_message(self) -> None:
        """Test welcome message generation."""
        message = MessageFactory.welcome("John")
        assert "John" in message
        assert "Football Analytics Platform" in message

    def test_main_menu_message(self) -> None:
        """Test main menu message generation."""
        message = MessageFactory.main_menu()
        assert "ГОЛОВНЕ МЕНЮ" in message
        assert "Матчі" in message

    def test_error_message(self) -> None:
        """Test error message generation."""
        message = MessageFactory.error_message("Something went wrong")
        assert "Помилка" in message
        assert "Something went wrong" in message

    def test_loading_message(self) -> None:
        """Test loading message generation."""
        message = MessageFactory.loading("Matches")
        assert "Завантаження" in message
        assert "Matches" in message

    def test_success_message(self) -> None:
        """Test success message generation."""
        message = MessageFactory.success("Done")
        assert "Успішно" in message
        assert "Done" in message

    def test_confirmation_message(self) -> None:
        """Test confirmation message generation."""
        message = MessageFactory.confirmation("Are you sure?")
        assert "Підтвердження" in message
        assert "Are you sure?" in message

    def test_separator(self) -> None:
        """Test separator constant."""
        assert "━" in MessageFactory.SEPARATOR
