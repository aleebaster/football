"""Tests for CallbackDataFactory."""

from app.telegram.callbacks import (
    AICallback,
    CallbackDataFactory,
    HelpCallback,
    MenuCallback,
    SettingsCallback,
    SignalsCallback,
    StatsCallback,
)


class TestCallbackDataFactory:
    """Tests for CallbackDataFactory."""

    def test_validate_valid_callback(self) -> None:
        """Test validation of valid callback data."""
        assert CallbackDataFactory.validate("menu:main") is True
        assert CallbackDataFactory.validate("signals:active") is True
        assert CallbackDataFactory.validate("ai:predictions") is True

    def test_validate_invalid_callback(self) -> None:
        """Test validation of invalid callback data."""
        assert CallbackDataFactory.validate("") is False
        assert CallbackDataFactory.validate("invalid") is False
        assert CallbackDataFactory.validate("unknown:data") is False

    def test_create_callback(self) -> None:
        """Test callback creation."""
        result = CallbackDataFactory.create("menu", "main")
        assert result == "menu:main"

    def test_parse_callback(self) -> None:
        """Test callback parsing."""
        category, action = CallbackDataFactory.parse("signals:active")
        assert category == "signals"
        assert action == "active"

    def test_parse_single_part(self) -> None:
        """Test parsing callback with no action."""
        category, action = CallbackDataFactory.parse("menu")
        assert category == "menu"
        assert action == ""

    def test_callback_enums(self) -> None:
        """Test callback enum values."""
        assert MenuCallback.MAIN.value == "menu:main"
        assert MenuCallback.BACK.value == "menu:back"
        assert SignalsCallback.ACTIVE.value == "signals:active"
        assert AICallback.PREDICTIONS.value == "ai:predictions"
        assert StatsCallback.OVERVIEW.value == "stats:overview"
        assert SettingsCallback.LANGUAGE.value == "settings:language"
        assert HelpCallback.GUIDE.value == "help:guide"
