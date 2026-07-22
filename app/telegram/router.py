"""Auto-registering Router for Telegram handlers.

Handlers are automatically registered based on decorators.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from app.logging import get_logger

logger = get_logger(__name__)


class Router:
    """Auto-registering router for Telegram handlers."""

    def __init__(self, name: str = "default") -> None:
        """Initialize router.

        Args:
            name: Router name for identification.
        """
        self.name = name
        self._command_handlers: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._callback_handlers: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._message_handlers: list[tuple[Callable[..., Awaitable[Any]], Any]] = []
        self._middlewares: list[Callable[..., Awaitable[Any]]] = []

    def command(self, command: str) -> Callable[..., Any]:
        """Decorator to register a command handler.

        Args:
            command: Command name (without /).

        Returns:
            Decorator function.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
            self._command_handlers[command] = func
            logger.debug(f"Registered command handler: /{command}")
            return func

        return decorator

    def callback(self, pattern: str | None = None) -> Callable[..., Any]:
        """Decorator to register a callback handler.

        Args:
            pattern: Optional callback pattern to match.

        Returns:
            Decorator function.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
            self._callback_handlers[pattern or func.__name__] = func
            logger.debug(f"Registered callback handler: {pattern or func.__name__}")
            return func

        return decorator

    def message(self, filters: Any = None) -> Callable[..., Any]:
        """Decorator to register a message handler.

        Args:
            filters: Optional filters to apply.

        Returns:
            Decorator function.
        """

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
            self._message_handlers.append((func, filters))
            logger.debug(f"Registered message handler: {func.__name__}")
            return func

        return decorator

    def middleware(
        self, func: Callable[..., Awaitable[Any]]
    ) -> Callable[..., Awaitable[Any]]:
        """Add middleware to the router.

        Args:
            func: Middleware function.

        Returns:
            The middleware function.
        """
        self._middlewares.append(func)
        logger.debug(f"Added middleware: {func.__name__}")
        return func

    async def execute_with_middleware(
        self,
        handler: Callable[..., Awaitable[Any]],
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        **kwargs: Any,
    ) -> Any:
        """Execute handler with middleware chain.

        Args:
            handler: Handler function to execute.
            update: Telegram update.
            context: Bot context.
            **kwargs: Additional arguments.

        Returns:
            Handler result.
        """
        # Execute pre-middleware
        for mw in self._middlewares:
            if hasattr(mw, "pre_process"):
                await mw.pre_process(update, context)

        try:
            result = await handler(update, context, **kwargs)
        except Exception as e:
            # Execute error middleware
            for mw in self._middlewares:
                if hasattr(mw, "on_error"):
                    await mw.on_error(update, context, e)
            raise
        finally:
            # Execute post-middleware
            for mw in self._middlewares:
                if hasattr(mw, "post_process"):
                    await mw.post_process(update, context)

        return result

    def get_command_handlers(self) -> dict[str, Callable[..., Awaitable[Any]]]:
        """Get all registered command handlers.

        Returns:
            Dictionary of command handlers.
        """
        return dict(self._command_handlers)

    def get_callback_handlers(self) -> dict[str, Callable[..., Awaitable[Any]]]:
        """Get all registered callback handlers.

        Returns:
            Dictionary of callback handlers.
        """
        return dict(self._callback_handlers)


# Global router instance
router = Router(name="main")
