"""Prediction Service — provides prediction data."""

from app.application.dto.prediction_dto import PredictionDTO, PredictionSummaryDTO
from app.application.mapper import Mapper
from app.core.container import get_container
from app.logging import get_logger
from app.prediction.models import PredictionRequest

logger = get_logger(__name__)


class PredictionService:
    """Provides prediction data through the Prediction Engine."""

    async def get_prediction(
        self,
        fixture_id: int,
        home_team_id: int = 0,
        away_team_id: int = 0,
        home_team: str = "",
        away_team: str = "",
    ) -> PredictionDTO:
        container = get_container()
        engine = container.prediction_engine

        try:
            request = PredictionRequest(
                fixture_id=fixture_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                force_refresh=False,
            )
            result = await engine.predict(request)
            return Mapper.to_prediction_dto(
                result, home_team=home_team, away_team=away_team
            )
        except Exception:
            logger.warning(
                "Failed to generate prediction for fixture %d",
                fixture_id,
                exc_info=True,
            )
            return PredictionDTO(
                fixture_id=fixture_id,
                home_team=home_team,
                away_team=away_team,
            )

    async def get_prediction_summary(
        self,
        fixture_id: int,
        home_team_id: int = 0,
        away_team_id: int = 0,
        home_team: str = "",
        away_team: str = "",
    ) -> PredictionSummaryDTO:
        container = get_container()
        engine = container.prediction_engine

        try:
            request = PredictionRequest(
                fixture_id=fixture_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                force_refresh=False,
            )
            result = await engine.predict(request)
            return Mapper.to_prediction_summary_dto(
                fixture_id, result, home_team=home_team, away_team=away_team
            )
        except Exception:
            logger.warning(
                "Failed to generate prediction summary for fixture %d",
                fixture_id,
                exc_info=True,
            )
            return PredictionSummaryDTO(
                fixture_id=fixture_id,
                home_team=home_team,
                away_team=away_team,
            )
