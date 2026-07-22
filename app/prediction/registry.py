"""Registry for prediction market predictors."""

from app.logging import get_logger
from app.prediction.interfaces import BasePredictor
from app.prediction.models import PredictionMarket

logger = get_logger(__name__)


class PredictorRegistry:
    """Registry that manages all available market predictors."""

    def __init__(self) -> None:
        self._predictors: dict[PredictionMarket, BasePredictor] = {}

    def register(self, predictor: BasePredictor) -> None:
        self._predictors[predictor.market] = predictor
        logger.debug(f"Registered predictor: {predictor.market.value}")

    def get(self, market: PredictionMarket) -> BasePredictor | None:
        return self._predictors.get(market)

    def get_all(self) -> list[BasePredictor]:
        return list(self._predictors.values())

    def get_supported_markets(self) -> list[PredictionMarket]:
        return list(self._predictors.keys())

    def __contains__(self, market: PredictionMarket) -> bool:
        return market in self._predictors

    def __len__(self) -> int:
        return len(self._predictors)
