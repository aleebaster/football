"""Registry for signal generators."""

from app.logging import get_logger
from app.prediction.models import PredictionMarket
from app.signals.interfaces import BaseSignalGenerator

logger = get_logger(__name__)


class SignalGeneratorRegistry:
    """Registry that manages all available signal generators."""

    def __init__(self) -> None:
        self._generators: dict[PredictionMarket, BaseSignalGenerator] = {}

    def register(
        self, generator: BaseSignalGenerator, market: PredictionMarket
    ) -> None:
        """Register a signal generator for a market."""
        self._generators[market] = generator
        logger.debug(f"Registered signal generator for {market.value}")

    def get(self, market: PredictionMarket) -> BaseSignalGenerator | None:
        """Get generator for a market."""
        return self._generators.get(market)

    def get_all(self) -> dict[PredictionMarket, BaseSignalGenerator]:
        """Get all registered generators."""
        return dict(self._generators)

    def get_supported_markets(self) -> list[PredictionMarket]:
        """Get all supported markets."""
        return list(self._generators.keys())

    def __contains__(self, market: PredictionMarket) -> bool:
        return market in self._generators

    def __len__(self) -> int:
        return len(self._generators)
