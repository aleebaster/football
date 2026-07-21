"""Market menu keyboard."""

from app.telegram.callbacks import MarketCallback, MenuCallback
from app.telegram.keyboards.factory import create_inline_keyboard


def get_market_menu_keyboard() -> object:
    """Get market submenu keyboard."""
    return create_inline_keyboard(
        [
            [
                ("📊 Live Odds", MarketCallback.LIVE_ODDS.value),
                ("📉 Market Movers", MarketCallback.MOVERS.value),
            ],
            [
                ("🔥 Trending", MarketCallback.TRENDING.value),
                ("📊 Найбільші зміни", MarketCallback.CHANGES.value),
            ],
            [
                ("⬅️ Назад", MenuCallback.MAIN_MENU.value),
                ("🏠 Головне меню", MenuCallback.HOME.value),
            ],
        ]
    )
