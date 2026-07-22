"""Tests for NavigationManager."""

import pytest

from app.telegram.navigation import NavigationManager


@pytest.fixture
def nav_manager() -> NavigationManager:
    """Create a fresh NavigationManager for each test."""
    return NavigationManager()


class TestNavigationManager:
    """Tests for NavigationManager."""

    @pytest.mark.asyncio
    async def test_navigate(self, nav_manager: NavigationManager) -> None:
        """Test navigation to a screen."""
        callback_data, handler = await nav_manager.navigate(123, "menu:main")
        assert callback_data == "menu:main"

    @pytest.mark.asyncio
    async def test_go_back_empty_stack(self, nav_manager: NavigationManager) -> None:
        """Test go back with empty stack."""
        callback_data, handler = await nav_manager.go_back(123)
        assert callback_data == "menu:main"

    @pytest.mark.asyncio
    async def test_go_back_with_history(self, nav_manager: NavigationManager) -> None:
        """Test go back with navigation history."""
        await nav_manager.navigate(123, "signals:active")
        await nav_manager.navigate(123, "signals:history")

        callback_data, handler = await nav_manager.go_back(123)
        assert callback_data == "signals:active"

    @pytest.mark.asyncio
    async def test_go_home(self, nav_manager: NavigationManager) -> None:
        """Test go home clears stack."""
        await nav_manager.navigate(123, "signals:active")
        await nav_manager.navigate(123, "ai:predictions")

        callback_data, handler = await nav_manager.go_home(123)
        assert callback_data == "menu:main"
        assert len(nav_manager.get_breadcrumbs(123)) == 0

    @pytest.mark.asyncio
    async def test_breadcrumbs(self, nav_manager: NavigationManager) -> None:
        """Test breadcrumbs tracking."""
        await nav_manager.navigate(123, "signals:active")
        await nav_manager.navigate(123, "signals:history")

        breadcrumbs = nav_manager.get_breadcrumbs(123)
        assert len(breadcrumbs) == 2
        assert "signals:active" in breadcrumbs
        assert "signals:history" in breadcrumbs

    def test_register_screen(self, nav_manager: NavigationManager) -> None:
        """Test screen registration."""
        nav_manager.register_screen(
            name="signals",
            title="Сигнали",
            callback_data="signals:active",
            is_root=True,
        )

        assert "signals" in nav_manager._screens
        assert nav_manager._screens["signals"].title == "Сигнали"

    def test_register_handler(self, nav_manager: NavigationManager) -> None:
        """Test handler registration."""

        async def dummy_handler() -> None:
            pass

        nav_manager.register_handler("menu:main", dummy_handler)
        assert "menu:main" in nav_manager._handlers

    @pytest.mark.asyncio
    async def test_clear(self, nav_manager: NavigationManager) -> None:
        """Test clearing navigation state."""
        await nav_manager.navigate(123, "signals:active")
        nav_manager.clear(123)

        assert 123 not in nav_manager._states

    @pytest.mark.asyncio
    async def test_get_current_screen(self, nav_manager: NavigationManager) -> None:
        """Test getting current screen."""
        await nav_manager.navigate(123, "signals:active")
        current = nav_manager.get_current_screen(123)
        assert current == "signals:active"

    @pytest.mark.asyncio
    async def test_get_breadcrumb_text(self, nav_manager: NavigationManager) -> None:
        """Test breadcrumb text generation."""
        await nav_manager.navigate(123, "signals:active")
        text = nav_manager.get_breadcrumb_text(123)
        assert "🏠" in text
