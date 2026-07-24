"""Live Engine — Match Discovery finds upcoming, starting, and live matches.

Uses the Provider Layer to discover matches that need processing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.live.interfaces import MatchDiscoveryInterface
from app.live.models import LiveMatch, MatchState
from app.logging import get_logger
from app.providers.manager import ProviderManager
from app.providers.models import Fixture, FixtureStatus

logger = get_logger(__name__)

# Map provider fixture status to Live Engine match state
_STATUS_MAP: dict[str, MatchState] = {
    FixtureStatus.SCHEDULED.value: MatchState.SCHEDULED,
    FixtureStatus.TIMED.value: MatchState.SCHEDULED,
    FixtureStatus.IN_PLAY.value: MatchState.LIVE,
    FixtureStatus.PAUSED.value: MatchState.HALF_TIME,
    FixtureStatus.HALFTIME.value: MatchState.HALF_TIME,
    FixtureStatus.FINISHED.value: MatchState.FINISHED,
    FixtureStatus.SUSPENDED.value: MatchState.INTERRUPTED,
    FixtureStatus.POSTPONED.value: MatchState.POSTPONED,
    FixtureStatus.CANCELLED.value: MatchState.CANCELLED,
    FixtureStatus.AWARDED.value: MatchState.FINISHED,
}


def _fixture_to_live_match(fixture: Fixture) -> LiveMatch:
    """Convert a Provider Fixture to a LiveMatch."""
    state = _STATUS_MAP.get(fixture.status, MatchState.SCHEDULED)
    return LiveMatch(
        fixture_id=fixture.id,
        home_team_id=fixture.home_team_id or 0,
        home_team=fixture.home_team or "",
        away_team_id=fixture.away_team_id or 0,
        away_team=fixture.away_team or "",
        competition_id=fixture.competition_id,
        competition_name=fixture.competition_name,
        utc_date=fixture.utc_date,
        status=fixture.status,
        state=state,
        home_score=fixture.home_score,
        away_score=fixture.away_score,
    )


class MatchDiscovery(MatchDiscoveryInterface):
    """Discovers matches that need processing via the Provider Layer."""

    def __init__(self, provider_manager: ProviderManager) -> None:
        self._provider_manager = provider_manager

    async def discover(self) -> list[LiveMatch]:
        """Discover upcoming and live matches.

        Fetches fixtures that are scheduled, timed, or currently in play.
        """
        matches: list[LiveMatch] = []
        try:
            # Fetch live matches
            live_fixtures = await self._provider_manager.live()
            for fixture in live_fixtures:
                matches.append(_fixture_to_live_match(fixture))

            # Fetch upcoming fixtures (next 24 hours)
            now = datetime.now(UTC)
            upcoming = await self._provider_manager.fixtures(
                date_from=now.strftime("%Y-%m-%d"),
                date_to=(now + timedelta(hours=24)).strftime("%Y-%m-%d"),
                limit=100,
            )
            seen_ids = {m.fixture_id for m in matches}
            for fixture in upcoming:
                if fixture.id not in seen_ids:
                    live_match = _fixture_to_live_match(fixture)
                    if live_match.state in (
                        MatchState.SCHEDULED,
                        MatchState.STARTING,
                        MatchState.LIVE,
                        MatchState.HALF_TIME,
                        MatchState.SECOND_HALF,
                    ):
                        matches.append(live_match)

            logger.debug(f"Discovered {len(matches)} matches")
        except Exception as e:
            logger.warning(f"Match discovery failed: {e}")

        return matches

    async def get_live_matches(self) -> list[LiveMatch]:
        """Get currently live matches only."""
        try:
            fixtures = await self._provider_manager.live()
            return [_fixture_to_live_match(f) for f in fixtures]
        except Exception as e:
            logger.warning(f"Failed to fetch live matches: {e}")
            return []
