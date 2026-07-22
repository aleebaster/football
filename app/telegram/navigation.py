"""Navigation manager for Telegram bot.

Manages navigation stack, breadcrumbs, and screen registration.
All transitions should go through this manager.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Screen:
    """Screen definition for navigation."""

    name: str
    title: str
    callback_data: str
    parent: str | None = None
    is_root: bool = False


@dataclass
class NavigationState:
    """User's navigation state."""

    stack: list[str] = field(default_factory=list)
    current_screen: str = "menu:main"


class NavigationManager:
    """Manages navigation stack for users with breadcrumbs support."""

    def __init__(self) -> None:
        """Initialize navigation manager."""
        self._states: dict[int, NavigationState] = {}
        self._screens: dict[str, Screen] = {}
        self._handlers: dict[str, Callable[..., Awaitable[Any]]] = {}

    def register_screen(
        self,
        name: str,
        title: str,
        callback_data: str,
        parent: str | None = None,
        is_root: bool = False,
    ) -> None:
        """Register a screen for navigation.

        Args:
            name: Screen name identifier.
            title: Screen display title.
            callback_data: Callback data for this screen.
            parent: Parent screen name.
            is_root: Whether this is a root screen.
        """
        self._screens[name] = Screen(
            name=name,
            title=title,
            callback_data=callback_data,
            parent=parent,
            is_root=is_root,
        )

    def register_handler(
        self, callback_data: str, handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a handler for callback data.

        Args:
            callback_data: Callback data to handle.
            handler: Async handler function.
        """
        self._handlers[callback_data] = handler

    def _get_state(self, user_id: int) -> NavigationState:
        """Get or create navigation state for user.

        Args:
            user_id: User ID.

        Returns:
            NavigationState for the user.
        """
        if user_id not in self._states:
            self._states[user_id] = NavigationState()
        return self._states[user_id]

    async def navigate(
        self, user_id: int, callback_data: str
    ) -> tuple[str, Callable[..., Awaitable[Any]] | None]:
        """Navigate to a callback and return the handler.

        Args:
            user_id: User ID.
            callback_data: Target callback data.

        Returns:
            Tuple of (callback_data, handler).
        """
        state = self._get_state(user_id)

        # Don't push back/home to stack
        if callback_data not in ("menu:back", "menu:main", "menu:home"):
            state.stack.append(callback_data)
            state.current_screen = callback_data

        handler = self._handlers.get(callback_data)
        return callback_data, handler

    async def go_back(
        self, user_id: int
    ) -> tuple[str, Callable[..., Awaitable[Any]] | None]:
        """Go back in navigation stack.

        Args:
            user_id: User ID.

        Returns:
            Tuple of (callback_data, handler).
        """
        state = self._get_state(user_id)

        if not state.stack:
            # Go to main menu if stack is empty
            state.current_screen = "menu:main"
            return "menu:main", self._handlers.get("menu:main")

        # Pop current screen
        state.stack.pop()

        if not state.stack:
            state.current_screen = "menu:main"
            return "menu:main", self._handlers.get("menu:main")

        last = state.stack[-1]
        state.current_screen = last
        return last, self._handlers.get(last)

    async def go_home(
        self, user_id: int
    ) -> tuple[str, Callable[..., Awaitable[Any]] | None]:
        """Go to home menu.

        Args:
            user_id: User ID.

        Returns:
            Tuple of (callback_data, handler).
        """
        state = self._get_state(user_id)
        state.stack.clear()
        state.current_screen = "menu:main"
        return "menu:main", self._handlers.get("menu:main")

    def get_breadcrumbs(self, user_id: int) -> list[str]:
        """Get navigation breadcrumbs for user.

        Args:
            user_id: User ID.

        Returns:
            List of callback_data representing breadcrumbs.
        """
        state = self._get_state(user_id)
        return list(state.stack)

    def get_breadcrumb_text(self, user_id: int) -> str:
        """Get formatted breadcrumb text.

        Args:
            user_id: User ID.

        Returns:
            Formatted breadcrumb string.
        """
        crumbs = self.get_breadcrumbs(user_id)
        if not crumbs:
            return "🏠 Головне меню"

        breadcrumb_names = []
        for crumb in crumbs:
            screen = self._screens.get(crumb)
            if screen:
                breadcrumb_names.append(screen.title)
            else:
                # Extract name from callback data
                name = crumb.split(":")[-1] if ":" in crumb else crumb
                breadcrumb_names.append(name.replace("_", " ").title())

        return " → ".join(["🏠"] + breadcrumb_names)

    def clear(self, user_id: int) -> None:
        """Clear navigation state for user.

        Args:
            user_id: User ID.
        """
        self._states.pop(user_id, None)

    def get_current_screen(self, user_id: int) -> str:
        """Get current screen for user.

        Args:
            user_id: User ID.

        Returns:
            Current screen callback_data.
        """
        state = self._get_state(user_id)
        return state.current_screen


# Global navigation instance
navigation = NavigationManager()
