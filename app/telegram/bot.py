"""Telegram bot class.

Provides the main Telegram bot instance and configuration.
"""

from typing import Any

from telegram import Bot
from telegram.ext import Application

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class TelegramBot:
    """Main Telegram bot class.

    Provides:
        - Bot instance management
        - Application setup
        - Handler registration
    """

    def __init__(self) -> None:
        """Initialize the Telegram bot."""
        self._bot: Bot | None = None
        self._application: Application | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the bot and application."""
        if self._initialized:
            return

        self._application = (
            Application.builder()
            .token(settings.telegram.bot_token)
            .build()
        )
        self._bot = self._application.bot
        self._initialized = True
        logger.info("Telegram bot initialized")

    async def start(self) -> None:
        """Start the bot polling."""
        if not self._initialized:
            await self.initialize()

        if self._application:
            await self._application.initialize()
            await self._application.start()
            await self._application.updater.start_polling()
            logger.info("Telegram bot started polling")

    async def stop(self) -> None:
        """Stop the bot polling."""
        if self._application:
            await self._application.updater.stop()
            await self._application.stop()
            await self._application.shutdown()
            logger.info("Telegram bot stopped")

    @property
    def bot(self) -> Bot | None:
        """Get the bot instance."""
        return self._bot

    @property
    def application(self) -> Application | None:
        """Get the application instance."""
        return self._application

    def add_handler(self, handler: Any) -> None:
        """Add a handler to the application.

        Args:
            handler: Telegram handler to add.
        """
        if self._application:
            self._application.add_handler(handler)

    def add_handlers(self, handlers: dict[int, Any]) -> None:
        """Add multiple handlers to the application.

        Args:
            handlers: Dictionary of handler groups and handlers.
        """
        if self._application:
            self._application.add_handlers(handlers)
