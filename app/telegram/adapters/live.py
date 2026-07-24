"""Telegram Adapter for Live Engine events.

Pipeline:
    Live Event → Telegram Adapter → Telegram Platform

The Live Engine does NOT know about Telegram API.
This adapter bridges Live Events to Telegram notifications.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from app.live.events import LiveEvent
from app.logging import get_logger

logger = get_logger(__name__)

# Type for Telegram send function
TelegramSendFunc = Callable[[str], Coroutine[Any, Any, bool]]


class LiveTelegramAdapter:
    """Adapts Live Engine events to Telegram notifications.

    This adapter subscribes to the Live Engine's EventPublisher
    and converts events into human-readable Telegram messages.

    Usage:
        adapter = LiveTelegramAdapter(send_func)
        publisher.register(adapter.handle_event)
    """

    def __init__(self, send_func: TelegramSendFunc | None = None) -> None:
        self._send_func = send_func
        self._enabled = True
        self._events_handled: int = 0

    async def handle_event(self, event: LiveEvent) -> None:
        """Handle a live event and optionally send to Telegram."""
        if not self._enabled or self._send_func is None:
            return

        message = self._format_message(event)
        if message:
            try:
                await self._send_func(message)
                self._events_handled += 1
            except Exception as e:
                logger.warning(f"Failed to send Telegram notification: {e}")

    def _format_message(self, event: LiveEvent) -> str | None:
        """Format a live event into a Telegram message."""
        event_type = event.event_type

        if event_type == "match_started":
            home = event.data.get("home_team", "?")
            away = event.data.get("away_team", "?")
            return f"⚽ Match Started!\n{home} vs {away}"

        elif event_type == "prediction_updated":
            confidence = event.data.get("confidence", 0)
            return f"📊 Prediction Updated\nConfidence: {confidence:.1%}"

        elif event_type == "signal_created":
            market = event.data.get("market", "")
            outcome = event.data.get("outcome", "")
            return f"🎯 New Signal!\nMarket: {market}\nOutcome: {outcome}"

        elif event_type == "goal":
            team = event.data.get("team", "")
            player = event.data.get("player", "")
            minute = event.data.get("minute", 0)
            score_home = event.data.get("score_home", 0)
            score_away = event.data.get("score_away", 0)
            return (
                f"⚽ GOAL!\n"
                f"{team} - {player} ({minute}')\n"
                f"Score: {score_home} - {score_away}"
            )

        elif event_type == "match_finished":
            home = event.data.get("home_team", "?")
            away = event.data.get("away_team", "?")
            score_home = event.data.get("home_score", 0)
            score_away = event.data.get("away_score", 0)
            return f"🏁 Match Finished!\n{home} {score_home} - {score_away} {away}"

        elif event_type == "odds_changed":
            market = event.data.get("market", "")
            return f"📈 Odds Changed\nMarket: {market}"

        return None

    def enable(self) -> None:
        """Enable Telegram notifications."""
        self._enabled = True

    def disable(self) -> None:
        """Disable Telegram notifications."""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def events_handled(self) -> int:
        return self._events_handled
