"""Start command handler for Telegram bot.

Handles /start command with user creation/update.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.core.dependencies import get_cache_manager, get_database
from app.logging import get_logger
from app.telegram.factories import MessageFactory
from app.telegram.keyboards.factory import KeyboardFactory
from app.telegram.services.user import UserService

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command.

    Creates user if not exists, updates if exists, greets, and shows main menu.
    """
    if update.message is None or update.effective_user is None:
        return

    user = update.effective_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    language_code = user.language_code

    logger.info(f"Start command from user {username} ({user_id})")

    # Create or update user in database
    try:
        async for session in get_database():
            cache = get_cache_manager()
            user_service = UserService(session, cache)
            await user_service.create_or_update(
                telegram_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
            )
            break
    except Exception as e:
        logger.error(f"Failed to create/update user: {e}")

    # Get user's display name
    display_name = first_name or username or "Користувач"

    # Create welcome message
    welcome_text = MessageFactory.welcome(display_name)

    # Create main menu keyboard
    main_menu_keyboard = KeyboardFactory.create_inline_keyboard(
        [
            [
                ("⚽ Матчі", "signals:active"),
                ("📈 Прогнози", "ai:predictions"),
            ],
            [
                ("📊 Статистика", "stats:overview"),
                ("🔥 Live", "market:odds"),
            ],
            [
                ("📰 Новини", "help:guide"),
                ("⭐ Обране", "signals:favorites"),
            ],
            [
                ("⚙️ Налаштування", "settings:language"),
                ("ℹ️ Про бота", "help:guide"),
            ],
        ]
    )

    # Create reply keyboard
    reply_keyboard = KeyboardFactory.create_reply_keyboard(
        [["⚽ Матчі", "📈 Прогнози"], ["📊 Статистика", "🔥 Live"], ["🏠 Меню"]],
    )

    # Send welcome message with reply keyboard
    await update.message.reply_text(
        text=welcome_text,
        parse_mode="MarkdownV2",
        reply_markup=reply_keyboard,
    )

    # Send main menu with inline keyboard
    await update.message.reply_text(
        text="Оберіть розділ:",
        reply_markup=main_menu_keyboard,
    )

    logger.info(f"Welcome message sent to user {user_id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if update.message is None:
        return

    help_text = r"""ℹ️ *ДОПОМОГА*

━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 *Гід* — Як користуватися
❓ *FAQ* — Часті питання
📞 *Контакти* — Зв'язатися з нами

━━━━━━━━━━━━━━━━━━━━━━━━━━

_Ми завжди готові допомогти_ 👇"""

    keyboard = KeyboardFactory.create_back_home_keyboard()

    await update.message.reply_text(
        text=help_text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard,
    )
