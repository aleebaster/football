"""Prediction market predictors package."""

from app.prediction.predictors.asian_handicap import AsianHandicapPredictor
from app.prediction.predictors.btts import BTTSPredictor
from app.prediction.predictors.cards import CardsPredictor
from app.prediction.predictors.corners import CornersPredictor
from app.prediction.predictors.double_chance import DoubleChancePredictor
from app.prediction.predictors.first_goal import FirstGoalPredictor
from app.prediction.predictors.halftime import HalftimePredictor
from app.prediction.predictors.over_under import OverUnderPredictor
from app.prediction.predictors.winner import WinnerPredictor

ALL_PREDICTORS = [
    WinnerPredictor,
    DoubleChancePredictor,
    OverUnderPredictor,
    BTTSPredictor,
    AsianHandicapPredictor,
    CornersPredictor,
    CardsPredictor,
    FirstGoalPredictor,
    HalftimePredictor,
]

__all__ = [
    "ALL_PREDICTORS",
    "WinnerPredictor",
    "DoubleChancePredictor",
    "OverUnderPredictor",
    "BTTSPredictor",
    "AsianHandicapPredictor",
    "CornersPredictor",
    "CardsPredictor",
    "FirstGoalPredictor",
    "HalftimePredictor",
]
