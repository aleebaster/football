"""Signal Ranking — sorts signals by quality metrics."""

from app.logging import get_logger
from app.signals.models import Signal, SignalRank

logger = get_logger(__name__)


class SignalRanker:
    """Ranks signals by multiple quality criteria."""

    def rank(self, signals: list[Signal]) -> list[Signal]:
        """Rank signals by quality score.

        Args:
            signals: List of signals to rank.

        Returns:
            Ranked list with position and percentile set.
        """
        if not signals:
            return []

        # Sort by overall score (descending)
        sorted_signals = sorted(
            signals,
            key=lambda s: s.score.overall if s.score else 0.0,
            reverse=True,
        )

        # Assign ranks
        for idx, signal in enumerate(sorted_signals):
            percentile = 1.0 - (idx / len(sorted_signals))
            signal.rank = SignalRank(
                position=idx + 1,
                percentile=round(percentile, 3),
                comparison_score=signal.score.overall if signal.score else 0.0,
            )

        logger.debug(f"Ranked {len(signals)} signals")
        return sorted_signals
