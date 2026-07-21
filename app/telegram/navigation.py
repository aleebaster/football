"""Navigation manager for Telegram bot."""

from collections.abc import Awaitable, Callable
from typing import Any


class NavigationManager:
    """Manages navigation stack for users."""

    def __init__(self) -> None:
        """Initialize navigation manager."""
        self._stacks: dict[int, list[str]] = {}
        self._handlers: dict[str, Callable[..., Awaitable[Any]]] = {}

    def register_handler(self, callback_data: str, handler: Callable[..., Awaitable[Any]]) -> None:
        """Register a handler for callback data."""
        self._handlers[callback_data] = handler

    async def navigate(self, user_id: int, callback_data: str) -> tuple[str, Callable[..., Awaitable[Any]] | None]:
        """Navigate to a callback and return the handler."""
        if user_id not in self._stacks:
            self._stacks[user_id] = []

        if callback_data != "menu:back" and callback_data != "menu:main":
            self._stacks[user_id].append(callback_data)

        handler = self._handlers.get(callback_data)
        return callback_data, handler

    async def go_back(self, user_id: int) -> tuple[str, Callable[..., Awaitable[Any]] | None]:
        """Go back in navigation stack."""
        if user_id not in self._stacks or not self._stacks[user_id]:
            return "menu:main", self._handlers.get("menu:main")

        self._stacks[user_id].pop()

        if not self._stacks[user_id]:
            return "menu:main", self._handlers.get("menu:main")

        last = self._stacks[user_id][-1]
        return last, self._handlers.get(last)

    async def go_home(self, user_id: int) -> tuple[str, Callable[..., Awaitable[Any]] | None]:
        """Go to home menu."""
        self._stacks[user_id] = []
        return "menu:main", self._handlers.get("menu:main")

    def clear(self, user_id: int) -> None:
        """Clear navigation stack for user."""
        self._stacks.pop(user_id, None)


navigation = NavigationManager()
