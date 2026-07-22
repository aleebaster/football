"""MarkdownV2 utilities for Telegram bot.

Provides escape utility for MarkdownV2 formatting.
"""


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2.

    Characters that need escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !

    Args:
        text: Text to escape.

    Returns:
        Escaped text safe for MarkdownV2.
    """
    special_chars = r"_*[]()~`>#+-=|{}.!"
    result = []
    for char in text:
        if char in special_chars:
            result.append(f"\\{char}")
        else:
            result.append(char)
    return "".join(result)


def escape_markdown_v2_text(text: str) -> str:
    """Escape text for MarkdownV2, preserving formatting markers.

    This escapes the text content but allows Markdown formatting
    like *bold* and _italic_ to work.

    Args:
        text: Text to escape (content, not formatting).

    Returns:
        Escaped text.
    """
    # First escape backslashes that are already in the text
    text = text.replace("\\", "\\\\")
    # Then escape all special characters
    return escape_markdown_v2(text)


def bold(text: str) -> str:
    """Format text as bold.

    Args:
        text: Text to format.

    Returns:
        Bold formatted text.
    """
    return f"*{escape_markdown_v2(text)}*"


def italic(text: str) -> str:
    """Format text as italic.

    Args:
        text: Text to format.

    Returns:
        Italic formatted text.
    """
    return f"_{escape_markdown_v2(text)}_"


def code(text: str) -> str:
    """Format text as inline code.

    Args:
        text: Text to format.

    Returns:
        Code formatted text.
    """
    return f"`{escape_markdown_v2(text)}`"


def pre(text: str, language: str = "") -> str:
    """Format text as preformatted code block.

    Args:
        text: Text to format.
        language: Optional language for syntax highlighting.

    Returns:
        Preformatted text.
    """
    if language:
        return f"```{language}\n{text}\n```"
    return f"```\n{text}\n```"


def link(text: str, url: str) -> str:
    """Create a markdown link.

    Args:
        text: Link text.
        url: Link URL.

    Returns:
        Markdown link.
    """
    return f"[{escape_markdown_v2(text)}]({url})"
