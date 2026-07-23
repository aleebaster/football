"""Watchlist — manages user watchlists for signal filtering."""

from app.logging import get_logger
from app.signals.models import Watchlist

logger = get_logger(__name__)


class WatchlistManager:
    """Manages user watchlists for filtering signals."""

    def __init__(self) -> None:
        self._watchlists: dict[int, Watchlist] = {}

    def get(self, user_id: int) -> Watchlist:
        """Get watchlist for a user.

        Args:
            user_id: User ID.

        Returns:
            User's watchlist (empty if not set).
        """
        return self._watchlists.get(
            user_id,
            Watchlist(user_id=user_id),
        )

    def set(self, watchlist: Watchlist) -> None:
        """Set watchlist for a user.

        Args:
            watchlist: Watchlist to set.
        """
        self._watchlists[watchlist.user_id] = watchlist
        logger.debug(f"Updated watchlist for user {watchlist.user_id}")

    def add_team(self, user_id: int, team_id: int) -> None:
        """Add a team to user's watchlist.

        Args:
            user_id: User ID.
            team_id: Team ID to add.
        """
        wl = self.get(user_id)
        if team_id not in wl.teams:
            wl.teams.append(team_id)
            self.set(wl)
            logger.debug(f"Added team {team_id} to user {user_id} watchlist")

    def remove_team(self, user_id: int, team_id: int) -> None:
        """Remove a team from user's watchlist.

        Args:
            user_id: User ID.
            team_id: Team ID to remove.
        """
        wl = self.get(user_id)
        if team_id in wl.teams:
            wl.teams.remove(team_id)
            self.set(wl)

    def add_league(self, user_id: int, league_id: int) -> None:
        """Add a league to user's watchlist.

        Args:
            user_id: User ID.
            league_id: League ID to add.
        """
        wl = self.get(user_id)
        if league_id not in wl.leagues:
            wl.leagues.append(league_id)
            self.set(wl)

    def remove_league(self, user_id: int, league_id: int) -> None:
        """Remove a league from user's watchlist.

        Args:
            user_id: User ID.
            league_id: League ID to remove.
        """
        wl = self.get(user_id)
        if league_id in wl.leagues:
            wl.leagues.remove(league_id)
            self.set(wl)

    def add_fixture(self, user_id: int, fixture_id: int) -> None:
        """Add a fixture to user's watchlist.

        Args:
            user_id: User ID.
            fixture_id: Fixture ID to add.
        """
        wl = self.get(user_id)
        if fixture_id not in wl.fixtures:
            wl.fixtures.append(fixture_id)
            self.set(wl)

    def remove_fixture(self, user_id: int, fixture_id: int) -> None:
        """Remove a fixture from user's watchlist.

        Args:
            user_id: User ID.
            fixture_id: Fixture ID to remove.
        """
        wl = self.get(user_id)
        if fixture_id in wl.fixtures:
            wl.fixtures.remove(fixture_id)
            self.set(wl)

    def add_tournament(self, user_id: int, tournament_id: int) -> None:
        """Add a tournament to user's watchlist.

        Args:
            user_id: User ID.
            tournament_id: Tournament ID to add.
        """
        wl = self.get(user_id)
        if tournament_id not in wl.tournaments:
            wl.tournaments.append(tournament_id)
            self.set(wl)

    def remove_tournament(self, user_id: int, tournament_id: int) -> None:
        """Remove a tournament from user's watchlist.

        Args:
            user_id: User ID.
            tournament_id: Tournament ID to remove.
        """
        wl = self.get(user_id)
        if tournament_id in wl.tournaments:
            wl.tournaments.remove(tournament_id)
            self.set(wl)

    def matches_watchlist(
        self,
        user_id: int,
        fixture_id: int,
        home_team_id: int,
        away_team_id: int,
        competition_id: int | None = None,
    ) -> bool:
        """Check if a fixture matches user's watchlist.

        If watchlist is empty, everything matches.

        Args:
            user_id: User ID.
            fixture_id: Fixture ID.
            home_team_id: Home team ID.
            away_team_id: Away team ID.
            competition_id: Optional competition/league ID.

        Returns:
            True if fixture matches watchlist or watchlist is empty.
        """
        wl = self.get(user_id)

        # Empty watchlist = everything matches
        if not wl.teams and not wl.leagues and not wl.fixtures and not wl.tournaments:
            return True

        # Check fixture
        if wl.fixtures and fixture_id in wl.fixtures:
            return True

        # Check teams
        if wl.teams and (home_team_id in wl.teams or away_team_id in wl.teams):
            return True

        # Check leagues
        if wl.leagues and competition_id and competition_id in wl.leagues:
            return True

        # If watchlist has entries but none matched
        return False

    def delete(self, user_id: int) -> bool:
        """Delete watchlist for a user.

        Args:
            user_id: User ID.

        Returns:
            True if deleted, False if not found.
        """
        if user_id in self._watchlists:
            del self._watchlists[user_id]
            return True
        return False
