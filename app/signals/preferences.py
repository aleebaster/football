"""User Preferences — manages user signal preferences."""

from app.logging import get_logger
from app.prediction.models import PredictionMarket, RiskLevel
from app.signals.models import UserPreferences

logger = get_logger(__name__)

# Default preferences
DEFAULT_PREFERENCES = UserPreferences(
    user_id=0,
    min_confidence=0.5,
    max_risk=RiskLevel.HIGH,
    allowed_markets=None,
    notification_start_hour=8,
    notification_end_hour=23,
    timezone="UTC",
    language="en",
    enabled=True,
)


class PreferencesManager:
    """Manages user signal preferences."""

    def __init__(self) -> None:
        self._preferences: dict[int, UserPreferences] = {}

    def get(self, user_id: int) -> UserPreferences:
        """Get preferences for a user.

        Args:
            user_id: User ID.

        Returns:
            User preferences (default if not set).
        """
        return self._preferences.get(
            user_id, DEFAULT_PREFERENCES.model_copy(update={"user_id": user_id})
        )

    def set(self, preferences: UserPreferences) -> None:
        """Set preferences for a user.

        Args:
            preferences: User preferences to set.
        """
        self._preferences[preferences.user_id] = preferences
        logger.debug(f"Updated preferences for user {preferences.user_id}")

    def update(
        self,
        user_id: int,
        **kwargs: object,
    ) -> UserPreferences:
        """Update specific fields of user preferences.

        Args:
            user_id: User ID.
            **kwargs: Fields to update.

        Returns:
            Updated preferences.
        """
        current = self.get(user_id)
        updated_data = current.model_dump()
        updated_data.update(kwargs)
        updated = UserPreferences(**updated_data)
        self.set(updated)
        return updated

    def add_favorite_team(self, user_id: int, team_id: int) -> None:
        """Add a team to user's favorites.

        Args:
            user_id: User ID.
            team_id: Team ID to add.
        """
        prefs = self.get(user_id)
        if team_id not in prefs.favorite_teams:
            prefs.favorite_teams.append(team_id)
            self.set(prefs)
            logger.debug(f"Added team {team_id} to user {user_id} favorites")

    def remove_favorite_team(self, user_id: int, team_id: int) -> None:
        """Remove a team from user's favorites.

        Args:
            user_id: User ID.
            team_id: Team ID to remove.
        """
        prefs = self.get(user_id)
        if team_id in prefs.favorite_teams:
            prefs.favorite_teams.remove(team_id)
            self.set(prefs)
            logger.debug(f"Removed team {team_id} from user {user_id} favorites")

    def add_favorite_league(self, user_id: int, league_id: int) -> None:
        """Add a league to user's favorites.

        Args:
            user_id: User ID.
            league_id: League ID to add.
        """
        prefs = self.get(user_id)
        if league_id not in prefs.favorite_leagues:
            prefs.favorite_leagues.append(league_id)
            self.set(prefs)

    def remove_favorite_league(self, user_id: int, league_id: int) -> None:
        """Remove a league from user's favorites.

        Args:
            user_id: User ID.
            league_id: League ID to remove.
        """
        prefs = self.get(user_id)
        if league_id in prefs.favorite_leagues:
            prefs.favorite_leagues.remove(league_id)
            self.set(prefs)

    def set_allowed_markets(
        self,
        user_id: int,
        markets: list[PredictionMarket] | None,
    ) -> None:
        """Set allowed markets for a user.

        Args:
            user_id: User ID.
            markets: List of allowed markets, or None for all.
        """
        prefs = self.get(user_id)
        prefs.allowed_markets = markets
        self.set(prefs)

    def set_quiet_hours(
        self,
        user_id: int,
        start_hour: int,
        end_hour: int,
    ) -> None:
        """Set quiet hours for notifications.

        Args:
            user_id: User ID.
            start_hour: Start hour (0-23).
            end_hour: End hour (0-23).
        """
        prefs = self.get(user_id)
        prefs.notification_start_hour = start_hour
        prefs.notification_end_hour = end_hour
        self.set(prefs)

    def delete(self, user_id: int) -> bool:
        """Delete preferences for a user.

        Args:
            user_id: User ID.

        Returns:
            True if deleted, False if not found.
        """
        if user_id in self._preferences:
            del self._preferences[user_id]
            logger.debug(f"Deleted preferences for user {user_id}")
            return True
        return False

    def get_all(self) -> dict[int, UserPreferences]:
        """Get all user preferences.

        Returns:
            Dictionary of user_id to preferences.
        """
        return dict(self._preferences)
