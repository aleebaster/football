"""Tests for Localization."""

import pytest

from app.telegram.localization import (
    Locale,
    LocalizationManager,
    create_localization_manager,
)


@pytest.fixture
def loc_manager() -> LocalizationManager:
    """Create a fresh LocalizationManager for each test."""
    return create_localization_manager()


class TestLocale:
    """Tests for Locale."""

    def test_locale_creation(self) -> None:
        """Test locale creation."""
        locale = Locale(code="uk", name="Ukrainian", native_name="Українська")
        assert locale.code == "uk"
        assert locale.name == "Ukrainian"

    def test_load_strings(self) -> None:
        """Test loading translation strings."""
        locale = Locale(code="test", name="Test", native_name="Test")
        locale.load({"hello": "Привіт", "bye": "До побачення"})

        assert locale.t("hello") == "Привіт"
        assert locale.t("bye") == "До побачення"

    def test_t_with_formatting(self) -> None:
        """Test translation with formatting."""
        locale = Locale(code="test", name="Test", native_name="Test")
        locale.load({"greeting": "Hello, {name}!"})

        result = locale.t("greeting", name="World")
        assert result == "Hello, World!"

    def test_t_missing_key(self) -> None:
        """Test translation with missing key returns key."""
        locale = Locale(code="test", name="Test", native_name="Test")
        result = locale.t("missing_key")
        assert result == "missing_key"


class TestLocalizationManager:
    """Tests for LocalizationManager."""

    def test_get_locale_default(self, loc_manager: LocalizationManager) -> None:
        """Test getting default locale."""
        locale = loc_manager.get_locale()
        assert locale.code == "uk"

    def test_get_locale_by_code(self, loc_manager: LocalizationManager) -> None:
        """Test getting locale by code."""
        locale = loc_manager.get_locale("en")
        assert locale.code == "en"

    def test_translate(self, loc_manager: LocalizationManager) -> None:
        """Test translation."""
        result = loc_manager.t("back", language="uk")
        assert "Назад" in result

    def test_set_user_language(self, loc_manager: LocalizationManager) -> None:
        """Test setting user language."""
        loc_manager.set_user_language(123, "en")
        assert loc_manager.get_user_language(123) == "en"

    def test_get_user_language_default(self, loc_manager: LocalizationManager) -> None:
        """Test getting default language for unknown user."""
        lang = loc_manager.get_user_language(999)
        assert lang == "uk"

    def test_get_available_languages(self, loc_manager: LocalizationManager) -> None:
        """Test getting available languages."""
        languages = loc_manager.get_available_languages()
        assert len(languages) >= 4
        codes = [lang["code"] for lang in languages]
        assert "uk" in codes
        assert "en" in codes
        assert "pl" in codes
        assert "de" in codes

    def test_add_locale(self, loc_manager: LocalizationManager) -> None:
        """Test adding a new locale."""
        new_locale = Locale(code="fr", name="French", native_name="Français")
        new_locale.load({"hello": "Bonjour"})
        loc_manager.add_locale(new_locale)

        locale = loc_manager.get_locale("fr")
        assert locale.code == "fr"
        assert locale.t("hello") == "Bonjour"
