"""Tests for Markdown utilities."""

from app.telegram.markdown import (
    bold,
    code,
    escape_markdown_v2,
    escape_markdown_v2_text,
    italic,
    link,
)


class TestMarkdownUtilities:
    """Tests for Markdown utilities."""

    def test_escape_markdown_v2(self) -> None:
        """Test escaping special characters."""
        text = "Hello *world*"
        escaped = escape_markdown_v2(text)
        assert "\\*" in escaped

    def test_escape_multiple_chars(self) -> None:
        """Test escaping multiple special characters."""
        text = "Test _italic_ [link](url)"
        escaped = escape_markdown_v2(text)
        assert "\\_" in escaped
        assert "\\[" in escaped

    def test_escape_markdown_v2_text(self) -> None:
        """Test escaping text content."""
        text = "Normal text"
        escaped = escape_markdown_v2_text(text)
        assert escaped == "Normal text"

    def test_bold_formatting(self) -> None:
        """Test bold formatting."""
        result = bold("test")
        assert result == "*test*"

    def test_bold_escapes_content(self) -> None:
        """Test bold escapes special chars."""
        result = bold("test *bold*")
        assert "\\*" in result

    def test_italic_formatting(self) -> None:
        """Test italic formatting."""
        result = italic("test")
        assert result == "_test_"

    def test_code_formatting(self) -> None:
        """Test code formatting."""
        result = code("test")
        assert result == "`test`"

    def test_link_formatting(self) -> None:
        """Test link formatting."""
        result = link("click", "https://example.com")
        assert "[click](https://example.com)" in result

    def test_preserves_normal_text(self) -> None:
        """Test that normal text is preserved."""
        text = "Hello World 123"
        escaped = escape_markdown_v2(text)
        assert escaped == text
