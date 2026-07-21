"""Telegram bot class with platform architecture."""

from telegram.ext import Application, ApplicationBuilder

from app.config import settings
from app.logging import get_logger
from app.telegram.dispatcher import setup_dispatcher

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
        self._application: Application | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the bot and application."""
        if self._initialized:
            return

        self._application = (
            ApplicationBuilder().token(settings.telegram.bot_token).build()
        )

        # Setup all handlers
        setup_dispatcher(self._application)

        self._initialized = True
        logger.info("Telegram bot platform initialized")

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
    def application(self) -> Application | None:
        """Get the application instance."""
        return self._application
