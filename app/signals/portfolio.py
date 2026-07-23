"""Portfolio — manages user portfolio for tracking bets."""

from app.logging import get_logger
from app.signals.models import Portfolio

logger = get_logger(__name__)


class PortfolioManager:
    """Manages user portfolios for tracking bets."""

    def __init__(self) -> None:
        self._portfolios: dict[int, Portfolio] = {}

    def get(self, user_id: int) -> Portfolio:
        """Get portfolio for a user.

        Args:
            user_id: User ID.

        Returns:
            User's portfolio (empty if not set).
        """
        return self._portfolios.get(
            user_id,
            Portfolio(user_id=user_id),
        )

    def set(self, portfolio: Portfolio) -> None:
        """Set portfolio for a user.

        Args:
            portfolio: Portfolio to set.
        """
        self._portfolios[portfolio.user_id] = portfolio
        logger.debug(f"Updated portfolio for user {portfolio.user_id}")

    def add_bet(self, user_id: int, signal_id: str, stake: float) -> None:
        """Add a bet to user's portfolio.

        Args:
            user_id: User ID.
            signal_id: Signal ID.
            stake: Bet stake amount.
        """
        portfolio = self.get(user_id)
        if signal_id not in portfolio.active_bets:
            portfolio.active_bets.append(signal_id)
            portfolio.total_stake += stake
            self.set(portfolio)
            logger.debug(f"Added bet {signal_id} to user {user_id} portfolio")

    def resolve_bet(
        self,
        user_id: int,
        signal_id: str,
        pnl: float,
        is_win: bool,
    ) -> None:
        """Resolve a bet in user's portfolio.

        Args:
            user_id: User ID.
            signal_id: Signal ID.
            pnl: Profit/loss amount.
            is_win: Whether the bet won.
        """
        portfolio = self.get(user_id)
        if signal_id in portfolio.active_bets:
            portfolio.active_bets.remove(signal_id)
            portfolio.total_pnl += pnl
            if is_win:
                portfolio.win_count += 1
            else:
                portfolio.loss_count += 1
            self.set(portfolio)
            logger.debug(
                f"Resolved bet {signal_id} for user {user_id}: pnl={pnl}, win={is_win}"
            )

    def get_win_rate(self, user_id: int) -> float:
        """Get win rate for a user.

        Args:
            user_id: User ID.

        Returns:
            Win rate as a float between 0 and 1.
        """
        portfolio = self.get(user_id)
        total = portfolio.win_count + portfolio.loss_count
        if total == 0:
            return 0.0
        return portfolio.win_count / total

    def get_roi(self, user_id: int) -> float:
        """Get ROI for a user.

        Args:
            user_id: User ID.

        Returns:
            ROI as a float.
        """
        portfolio = self.get(user_id)
        if portfolio.total_stake == 0:
            return 0.0
        return portfolio.total_pnl / portfolio.total_stake

    def get_active_bets(self, user_id: int) -> list[str]:
        """Get active bets for a user.

        Args:
            user_id: User ID.

        Returns:
            List of active bet signal IDs.
        """
        portfolio = self.get(user_id)
        return list(portfolio.active_bets)

    def delete(self, user_id: int) -> bool:
        """Delete portfolio for a user.

        Args:
            user_id: User ID.

        Returns:
            True if deleted, False if not found.
        """
        if user_id in self._portfolios:
            del self._portfolios[user_id]
            return True
        return False
