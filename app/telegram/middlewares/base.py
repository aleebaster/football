"""Base middleware class for Telegram bot."""

from abc import ABC, abstractmethod

from telegram import Update
from telegram.ext import ContextTypes


class BaseMiddleware(ABC):
    """Abstract base class for all middlewares."""

    @abstractmethod
    async def pre_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Pre-process hook called before handler execution.

        Args:
            update: Telegram update.
            context: Bot context.
        """
        ...

    @abstractmethod
    async def post_process(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Post-process hook called after handler execution.

        Args:
            update: Telegram update.
            context: Bot context.
        """
        ...

    def on_error(  # noqa: B027
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception,
    ) -> None:
        """Optional error hook. Override in subclasses to handle errors."""
        pass
