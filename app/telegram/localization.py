"""Localization system for Telegram bot.

Supports multiple languages with easy extensibility.
Current: Ukrainian (uk)
Architecture allows adding: en, pl, de, etc.
"""

from typing import Any


class Locale:
    """Locale container for a single language."""

    def __init__(self, code: str, name: str, native_name: str) -> None:
        """Initialize locale.

        Args:
            code: Language code (e.g., 'uk').
            name: Language name in English.
            native_name: Language name in native script.
        """
        self.code = code
        self.name = name
        self.native_name = native_name
        self._strings: dict[str, str] = {}

    def load(self, strings: dict[str, str]) -> None:
        """Load translation strings.

        Args:
            strings: Dictionary of key-value translation pairs.
        """
        self._strings.update(strings)

    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a key with optional formatting.

        Args:
            key: Translation key.
            **kwargs: Format arguments.

        Returns:
            Translated string, or key if not found.
        """
        template = self._strings.get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, IndexError):
                return template
        return template


class LocalizationManager:
    """Manages multiple locales and provides translation access."""

    def __init__(self, default_language: str = "uk") -> None:
        """Initialize localization manager.

        Args:
            default_language: Default language code.
        """
        self._locales: dict[str, Locale] = {}
        self._default_language = default_language
        self._current_languages: dict[int, str] = {}

    def add_locale(self, locale: Locale) -> None:
        """Add a locale.

        Args:
            locale: Locale instance to add.
        """
        self._locales[locale.code] = locale

    def get_locale(self, language_code: str | None = None) -> Locale:
        """Get locale by language code.

        Args:
            language_code: Language code, falls back to default.

        Returns:
            Locale instance.
        """
        code = language_code or self._default_language
        return self._locales.get(code, self._locales[self._default_language])

    def t(self, key: str, language: str | None = None, **kwargs: Any) -> str:
        """Translate a key.

        Args:
            key: Translation key.
            language: Language code override.
            **kwargs: Format arguments.

        Returns:
            Translated string.
        """
        locale = self.get_locale(language)
        return locale.t(key, **kwargs)

    def set_user_language(self, user_id: int, language: str) -> None:
        """Set preferred language for a user.

        Args:
            user_id: User ID.
            language: Language code.
        """
        self._current_languages[user_id] = language

    def get_user_language(self, user_id: int) -> str:
        """Get preferred language for a user.

        Args:
            user_id: User ID.

        Returns:
            Language code.
        """
        return self._current_languages.get(user_id, self._default_language)

    def get_available_languages(self) -> list[dict[str, str]]:
        """Get list of available languages.

        Returns:
            List of language info dicts.
        """
        return [
            {
                "code": locale.code,
                "name": locale.name,
                "native_name": locale.native_name,
            }
            for locale in self._locales.values()
        ]


def _create_uk_locale() -> Locale:
    """Create Ukrainian locale with all translations.

    Returns:
        Configured Ukrainian locale.
    """
    locale = Locale(code="uk", name="Ukrainian", native_name="Українська")
    locale.load(
        {
            # General
            "welcome": "⚡ *Football Analytics Platform*\n\n🏆 *Ласкаво просимо, {name}\\!*\n\n📊 *Аналіз у реальному часі*\n🧠 *AI\\-прогнози*\n📈 *Ринок ставок*",
            "main_menu": "🏠 *ГОЛОВНЕ МЕНЮ*",
            "select_section": "Оберіть розділ для переходу 👇",
            "back": "⬅️ Назад",
            "home": "🏠 Головне меню",
            "refresh": "🔄 Оновити",
            "cancel": "❌ Скасувати",
            "confirm": "✅ Підтвердити",
            # Sections
            "section_matches": "⚽ Матчі",
            "section_predictions": "📈 Прогнози",
            "section_stats": "📊 Статистика",
            "section_live": "🔥 Live",
            "section_news": "📰 Новини",
            "section_favorites": "⭐ Обране",
            "section_settings": "⚙️ Налаштування",
            "section_about": "ℹ️ Про бота",
            # Errors
            "error": "❌ Помилка",
            "error_general": "Сталася помилка. Спробуйте ще раз.",
            "error_not_found": "Не знайдено",
            # Success
            "success": "✅ Успішно\\!",
            "loading": "⏳ Завантаження\\.\\.\\.",
            # Settings
            "settings_language": "🌐 Оберіть мову",
            "settings_notifications": "🔔 Сповіщення",
            "settings_frequency": "⏰ Частота оновлень",
            "settings_theme": "🎨 Тема",
            # About
            "about_name": "Football Analytics Platform",
            "about_version": "Версія: {version}",
            "about_description": "AI платформа для аналізу футбольних матчів та ставок",
        }
    )
    return locale


def _create_en_locale() -> Locale:
    """Create English locale (placeholder).

    Returns:
        Configured English locale.
    """
    locale = Locale(code="en", name="English", native_name="English")
    locale.load(
        {
            "welcome": "⚡ *Football Analytics Platform*\n\n🏆 *Welcome, {name}\\!*\n\n📊 *Real\\-time analysis*\n🧠 *AI predictions*\n📈 *Betting market*",
            "main_menu": "🏠 *MAIN MENU*",
            "select_section": "Select a section 👇",
            "back": "⬅️ Back",
            "home": "🏠 Main menu",
            "error": "❌ Error",
            "error_general": "An error occurred. Please try again.",
        }
    )
    return locale


def _create_pl_locale() -> Locale:
    """Create Polish locale (placeholder).

    Returns:
        Configured Polish locale.
    """
    locale = Locale(code="pl", name="Polish", native_name="Polski")
    locale.load(
        {
            "welcome": "⚡ *Football Analytics Platform*\n\n🏆 *Witaj, {name}\\!*\n\n📊 *Analiza w czasie rzeczywistym*\n🧠 *Prognozy AI*\n📈 *Rynek zakładów*",
            "main_menu": "🏠 *GŁÓWNE MENU*",
            "select_section": "Wybierz sekcję 👇",
            "back": "⬅️ Wstecz",
            "home": "🏠 Menu główne",
        }
    )
    return locale


def _create_de_locale() -> Locale:
    """Create German locale (placeholder).

    Returns:
        Configured German locale.
    """
    locale = Locale(code="de", name="German", native_name="Deutsch")
    locale.load(
        {
            "welcome": "⚡ *Football Analytics Platform*\n\n🏆 *Willkommen, {name}\\!*\n\n📊 *Echtzeitanalyse*\n🧠 *KI\\-Vorhersagen*\n📈 *Wettmarkt*",
            "main_menu": "🏠 *HAUPTMENÜ*",
            "select_section": "Wählen Sie einen Bereich 👇",
            "back": "⬅️ Zurück",
            "home": "🏠 Hauptmenü",
        }
    )
    return locale


def create_localization_manager(default_language: str = "uk") -> LocalizationManager:
    """Create and configure the localization manager.

    Args:
        default_language: Default language code.

    Returns:
        Configured LocalizationManager with all locales.
    """
    manager = LocalizationManager(default_language=default_language)
    manager.add_locale(_create_uk_locale())
    manager.add_locale(_create_en_locale())
    manager.add_locale(_create_pl_locale())
    manager.add_locale(_create_de_locale())
    return manager


# Global localization instance
localization = create_localization_manager()
