"""Tests for Router."""

import pytest

from app.telegram.router import Router


@pytest.fixture
def test_router() -> Router:
    """Create a fresh Router for each test."""
    return Router(name="test")


class TestRouter:
    """Tests for Router."""

    def test_router_creation(self, test_router: Router) -> None:
        """Test router creation."""
        assert test_router.name == "test"

    def test_register_command(self, test_router: Router) -> None:
        """Test command registration via decorator."""

        @test_router.command("test")
        async def test_handler() -> None:
            pass

        handlers = test_router.get_command_handlers()
        assert "test" in handlers

    def test_register_callback(self, test_router: Router) -> None:
        """Test callback registration via decorator."""

        @test_router.callback("test:action")
        async def test_handler() -> None:
            pass

        handlers = test_router.get_callback_handlers()
        assert "test:action" in handlers

    def test_multiple_commands(self, test_router: Router) -> None:
        """Test registering multiple commands."""

        @test_router.command("start")
        async def start_handler() -> None:
            pass

        @test_router.command("help")
        async def help_handler() -> None:
            pass

        handlers = test_router.get_command_handlers()
        assert len(handlers) == 2
        assert "start" in handlers
        assert "help" in handlers
