"""AI analyzers subpackage."""

from app.ai.analyzers.fixtures import FixturesAnalyzer
from app.ai.analyzers.form import FormAnalyzer
from app.ai.analyzers.goals import GoalsAnalyzer
from app.ai.analyzers.h2h import H2HAnalyzer
from app.ai.analyzers.home_away import HomeAwayAnalyzer
from app.ai.analyzers.injuries import InjuriesAnalyzer
from app.ai.analyzers.momentum import MomentumAnalyzer
from app.ai.analyzers.odds import OddsAnalyzer
from app.ai.analyzers.referee import RefereeAnalyzer
from app.ai.analyzers.standings import StandingsAnalyzer
from app.ai.analyzers.suspensions import SuspensionsAnalyzer
from app.ai.analyzers.weather import WeatherAnalyzer
from app.ai.analyzers.xg import XGAnalyzer

ALL_ANALYZERS = [
    FormAnalyzer,
    StandingsAnalyzer,
    HomeAwayAnalyzer,
    H2HAnalyzer,
    GoalsAnalyzer,
    OddsAnalyzer,
    FixturesAnalyzer,
    MomentumAnalyzer,
    InjuriesAnalyzer,
    SuspensionsAnalyzer,
    WeatherAnalyzer,
    RefereeAnalyzer,
    XGAnalyzer,
]

__all__ = [
    "ALL_ANALYZERS",
    "FormAnalyzer",
    "StandingsAnalyzer",
    "HomeAwayAnalyzer",
    "H2HAnalyzer",
    "GoalsAnalyzer",
    "OddsAnalyzer",
    "FixturesAnalyzer",
    "MomentumAnalyzer",
    "InjuriesAnalyzer",
    "SuspensionsAnalyzer",
    "WeatherAnalyzer",
    "RefereeAnalyzer",
    "XGAnalyzer",
]
