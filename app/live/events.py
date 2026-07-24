"""Live Engine — Event models and event factory.

All events flow through the Publisher to subscribers (REST, Dashboard, Telegram, WebSocket).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class LiveEvent(BaseModel):
    """An event emitted by the Live Engine."""

    event_id: str = ""
    event_type: str = ""
    fixture_id: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data: dict[str, object] = Field(default_factory=dict)
    correlation_id: str | None = None
    worker_id: str | None = None


class MatchStartedEvent(LiveEvent):
    """Emitted when a match transitions to LIVE."""

    event_type: str = "match_started"


class PredictionUpdatedEvent(LiveEvent):
    """Emitted when predictions are updated for a live match."""

    event_type: str = "prediction_updated"


class SignalCreatedEvent(LiveEvent):
    """Emitted when a new signal is created for a live match."""

    event_type: str = "signal_created"


class SignalUpdatedEvent(LiveEvent):
    """Emitted when a signal is updated."""

    event_type: str = "signal_updated"


class GoalEvent(LiveEvent):
    """Emitted when a goal is scored."""

    event_type: str = "goal"


class OddsChangedEvent(LiveEvent):
    """Emitted when odds change significantly."""

    event_type: str = "odds_changed"


class MatchFinishedEvent(LiveEvent):
    """Emitted when a match finishes."""

    event_type: str = "match_finished"


class HeartbeatEvent(LiveEvent):
    """Periodic heartbeat event for health monitoring."""

    event_type: str = "heartbeat"


class EventFactory:
    """Factory for creating typed Live Events with correlation IDs."""

    @staticmethod
    def match_started(
        match: object, correlation_id: str | None = None
    ) -> MatchStartedEvent:
        from app.live.models import LiveMatch

        m = match if isinstance(match, LiveMatch) else None
        return MatchStartedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="match_started",
            fixture_id=m.fixture_id if m else 0,
            correlation_id=correlation_id,
            data={
                "home_team": m.home_team if m else "",
                "away_team": m.away_team if m else "",
                "competition": m.competition_name if m else "",
            },
        )

    @staticmethod
    def prediction_updated(
        fixture_id: int,
        confidence: float = 0.0,
        correlation_id: str | None = None,
    ) -> PredictionUpdatedEvent:
        return PredictionUpdatedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="prediction_updated",
            fixture_id=fixture_id,
            correlation_id=correlation_id,
            data={"confidence": confidence},
        )

    @staticmethod
    def signal_created(
        fixture_id: int,
        signal_id: str = "",
        market: str = "",
        outcome: str = "",
        correlation_id: str | None = None,
    ) -> SignalCreatedEvent:
        return SignalCreatedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="signal_created",
            fixture_id=fixture_id,
            correlation_id=correlation_id,
            data={"signal_id": signal_id, "market": market, "outcome": outcome},
        )

    @staticmethod
    def signal_updated(
        fixture_id: int,
        signal_id: str = "",
        correlation_id: str | None = None,
    ) -> SignalUpdatedEvent:
        return SignalUpdatedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="signal_updated",
            fixture_id=fixture_id,
            correlation_id=correlation_id,
            data={"signal_id": signal_id},
        )

    @staticmethod
    def goal(
        fixture_id: int,
        team: str = "",
        player: str = "",
        minute: int = 0,
        score_home: int = 0,
        score_away: int = 0,
        correlation_id: str | None = None,
    ) -> GoalEvent:
        return GoalEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="goal",
            fixture_id=fixture_id,
            correlation_id=correlation_id,
            data={
                "team": team,
                "player": player,
                "minute": minute,
                "score_home": score_home,
                "score_away": score_away,
            },
        )

    @staticmethod
    def odds_changed(
        fixture_id: int,
        market: str = "",
        correlation_id: str | None = None,
    ) -> OddsChangedEvent:
        return OddsChangedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="odds_changed",
            fixture_id=fixture_id,
            correlation_id=correlation_id,
            data={"market": market},
        )

    @staticmethod
    def match_finished(
        match: object,
        correlation_id: str | None = None,
    ) -> MatchFinishedEvent:
        from app.live.models import LiveMatch

        m = match if isinstance(match, LiveMatch) else None
        return MatchFinishedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="match_finished",
            fixture_id=m.fixture_id if m else 0,
            correlation_id=correlation_id,
            data={
                "home_team": m.home_team if m else "",
                "away_team": m.away_team if m else "",
                "home_score": m.home_score if m else 0,
                "away_score": m.away_score if m else 0,
            },
        )

    @staticmethod
    def heartbeat(
        active_matches: int = 0,
        workers: int = 0,
    ) -> HeartbeatEvent:
        return HeartbeatEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type="heartbeat",
            fixture_id=0,
            data={
                "active_matches": active_matches,
                "workers": workers,
            },
        )
