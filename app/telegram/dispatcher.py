"""Telegram bot dispatcher configuration.

Sets up all handlers and middleware.
"""

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
)

from app.logging import get_logger
from app.telegram.handlers.callbacks import callback_handler
from app.telegram.handlers.main_menu import (
    about_handler,
    favorites_handler,
    live_handler,
    main_menu_handler,
    matches_handler,
    news_handler,
    predictions_handler,
    settings_handler,
    stats_handler,
)
from app.telegram.handlers.start import help_command, start_command
from app.telegram.middlewares import (
    ErrorMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    TimingMiddleware,
    UserContextMiddleware,
)
from app.telegram.navigation import navigation

logger = get_logger(__name__)


def setup_dispatcher(application: Application) -> Application:  # type: ignore[type-arg]
    """Setup all handlers on the application.

    Args:
        application: Telegram Application instance.

    Returns:
        Configured Application.
    """
    # Initialize middlewares
    middlewares = [
        LoggingMiddleware(),
        ErrorMiddleware(),
        MetricsMiddleware(),
        TimingMiddleware(),
        UserContextMiddleware(),
    ]

    # Store middlewares in app data for access
    application.bot_data["middlewares"] = middlewares

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Register callback handlers with patterns
    application.add_handler(
        CallbackQueryHandler(main_menu_handler, pattern=r"^menu:main$")
    )
    application.add_handler(
        CallbackQueryHandler(matches_handler, pattern=r"^signals:active$")
    )
    application.add_handler(
        CallbackQueryHandler(predictions_handler, pattern=r"^ai:predictions$")
    )
    application.add_handler(
        CallbackQueryHandler(stats_handler, pattern=r"^stats:overview$")
    )
    application.add_handler(
        CallbackQueryHandler(live_handler, pattern=r"^market:odds$")
    )
    application.add_handler(CallbackQueryHandler(news_handler, pattern=r"^help:guide$"))
    application.add_handler(
        CallbackQueryHandler(favorites_handler, pattern=r"^signals:favorites$")
    )
    application.add_handler(
        CallbackQueryHandler(settings_handler, pattern=r"^settings:language$")
    )

    # Register catch-all callback handler (must be last)
    application.add_handler(CallbackQueryHandler(callback_handler))

    # Register handlers in navigation manager
    navigation.register_handler("menu:main", main_menu_handler)
    navigation.register_handler("menu:back", main_menu_handler)
    navigation.register_handler("menu:home", main_menu_handler)
    navigation.register_handler("signals:active", matches_handler)
    navigation.register_handler("ai:predictions", predictions_handler)
    navigation.register_handler("stats:overview", stats_handler)
    navigation.register_handler("market:odds", live_handler)
    navigation.register_handler("help:guide", news_handler)
    navigation.register_handler("signals:favorites", favorites_handler)
    navigation.register_handler("settings:language", settings_handler)
    navigation.register_handler("help:about", about_handler)

    logger.info("Dispatcher setup completed")
    return application
