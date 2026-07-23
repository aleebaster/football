"""Interfaces for Signal Engine components."""

from abc import ABC, abstractmethod
from typing import Any

from app.prediction.models import PredictionResult
from app.signals.models import Signal


class BaseSignalGenerator(ABC):
    """Abstract base class for all signal generators."""

    @abstractmethod
    async def generate(self, prediction: PredictionResult) -> list[Signal]:
        """Generate signals from a prediction result.

        Args:
            prediction: Prediction result from Prediction Engine.

        Returns:
            List of generated signals.
        """
        ...


class BaseSignalFilter(ABC):
    """Abstract base class for signal filters."""

    @abstractmethod
    def should_keep(self, signal: Signal) -> bool:
        """Determine if a signal should be kept.

        Args:
            signal: Signal to evaluate.

        Returns:
            True if signal should be kept, False otherwise.
        """
        ...


class BaseSignalScorer(ABC):
    """Abstract base class for signal scoring."""

    @abstractmethod
    def score(self, signal: Signal, context: dict[str, Any] | None = None) -> float:
        """Calculate score for a signal.

        Args:
            signal: Signal to score.
            context: Optional context data.

        Returns:
            Score value between 0 and 1.
        """
        ...


class BaseSignalRanker(ABC):
    """Abstract base class for signal ranking."""

    @abstractmethod
    def rank(self, signals: list[Signal]) -> list[Signal]:
        """Rank signals by quality.

        Args:
            signals: List of signals to rank.

        Returns:
            Ranked list of signals.
        """
        ...
