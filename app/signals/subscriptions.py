"""Subscriptions — manages signal subscriptions for users."""

from app.logging import get_logger
from app.prediction.models import PredictionMarket

logger = get_logger(__name__)


class Subscription:
    """Represents a user subscription to signals."""

    def __init__(
        self,
        user_id: int,
        fixture_id: int | None = None,
        market: PredictionMarket | None = None,
        team_id: int | None = None,
    ) -> None:
        self.user_id = user_id
        self.fixture_id = fixture_id
        self.market = market
        self.team_id = team_id


class SubscriptionManager:
    """Manages user signal subscriptions."""

    def __init__(self) -> None:
        self._subscriptions: dict[int, list[Subscription]] = {}

    def subscribe(self, subscription: Subscription) -> None:
        """Subscribe a user to signals."""
        if subscription.user_id not in self._subscriptions:
            self._subscriptions[subscription.user_id] = []
        self._subscriptions[subscription.user_id].append(subscription)
        logger.debug(f"User {subscription.user_id} subscribed to signals")

    def unsubscribe(self, user_id: int, subscription: Subscription) -> bool:
        """Unsubscribe a user from signals."""
        subs = self._subscriptions.get(user_id, [])
        for i, sub in enumerate(subs):
            if (
                sub.fixture_id == subscription.fixture_id
                and sub.market == subscription.market
                and sub.team_id == subscription.team_id
            ):
                subs.pop(i)
                return True
        return False

    def get_subscriptions(self, user_id: int) -> list[Subscription]:
        """Get all subscriptions for a user."""
        return list(self._subscriptions.get(user_id, []))

    def clear(self, user_id: int) -> None:
        """Clear all subscriptions for a user."""
        self._subscriptions.pop(user_id, None)

    def __len__(self) -> int:
        return sum(len(subs) for subs in self._subscriptions.values())
