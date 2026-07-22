"""Message factory for creating Telegram messages.

Centralizes all message templates, Markdown formatting, and system messages.
"""


class MessageFactory:
    """Factory for creating all bot messages."""

    # ══════════════════════════════════════════════════════════════════
    # SEPARATOR
    # ══════════════════════════════════════════════════════════════════

    SEPARATOR = "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    SEPARATOR_SHORT = "────────────────────────"

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape special characters for MarkdownV2.

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

    @staticmethod
    def bold(text: str) -> str:
        """Format text as bold.

        Args:
            text: Text to format.

        Returns:
            Bold formatted text.
        """
        return f"*{text}*"

    @staticmethod
    def italic(text: str) -> str:
        """Format text as italic.

        Args:
            text: Text to format.

        Returns:
            Italic formatted text.
        """
        return f"_{text}_"

    @staticmethod
    def code(text: str) -> str:
        """Format text as code.

        Args:
            text: Text to format.

        Returns:
            Code formatted text.
        """
        return f"`{text}`"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Create a markdown link.

        Args:
            text: Link text.
            url: Link URL.

        Returns:
            Markdown link.
        """
        return f"[{text}]({url})"

    @classmethod
    def welcome(cls, user_name: str) -> str:
        """Create welcome message.

        Args:
            user_name: User's name.

        Returns:
            Welcome message.
        """
        escaped_name = cls.escape_markdown(user_name)
        return f"""⚡ *Football Analytics Platform*

{cls.SEPARATOR}

🏆 *Ласкаво просимо, {escaped_name}\\!*

📊 *Аналіз у реальному часі*
🧠 *AI\\-прогнози*
📈 *Ринок ставок*

{cls.SEPARATOR}

Оберіть розділ меню 👇"""

    @classmethod
    def main_menu(cls) -> str:
        """Create main menu message.

        Returns:
            Main menu message.
        """
        return f"""🏠 *ГОЛОВНЕ МЕНЮ*

{cls.SEPARATOR}

⚽ *Матчі* — Пошук та аналіз
📈 *Прогнози* — AI\\-прогнози
📊 *Статистика* — Ваші дані
🔥 *Live* — Наживо
📰 *Новини* — Останні новини
⭐ *Обране* — Збережені матчі
⚙️ *Налаштування* — Конфігурація
ℹ️ *Про бота* — Інформація

{cls.SEPARATOR}

_Оберіть розділ для переходу_ 👇"""

    @classmethod
    def error_message(cls, error: str) -> str:
        """Create error message.

        Args:
            error: Error description.

        Returns:
            Error message.
        """
        escaped_error = cls.escape_markdown(error)
        return f"""❌ *Помилка*

{cls.SEPARATOR_SHORT}

{escaped_error}

{cls.SEPARATOR_SHORT}

_Спробуйте ще раз або зверніться до підтримки_"""

    @classmethod
    def loading(cls, section: str = "") -> str:
        """Create loading message.

        Args:
            section: Section being loaded.

        Returns:
            Loading message.
        """
        escaped_section = cls.escape_markdown(section) if section else ""
        text = "⏳ *Завантаження\\.\\.\\.*"
        if escaped_section:
            text += f"\n\n{escaped_section}"
        return text

    @classmethod
    def success(cls, message: str) -> str:
        """Create success message.

        Args:
            message: Success description.

        Returns:
            Success message.
        """
        escaped_message = cls.escape_markdown(message)
        return f"""✅ *Успішно\\!*

{cls.SEPARATOR_SHORT}

{escaped_message}

{cls.SEPARATOR_SHORT}"""

    @classmethod
    def confirmation(cls, question: str) -> str:
        """Create confirmation message.

        Args:
            question: Question to confirm.

        Returns:
            Confirmation message.
        """
        escaped_question = cls.escape_markdown(question)
        return f"""⚠️ *Підтвердження*

{cls.SEPARATOR_SHORT}

{escaped_question}

{cls.SEPARATOR_SHORT}"""


# Backward compatibility
WELCOME_TEXT = MessageFactory.welcome("Користувач")
MAIN_MENU_TEXT = MessageFactory.main_menu()
BACK_TEXT = "⬅️ Назад"
HOME_TEXT = "🏠 Головне меню"
