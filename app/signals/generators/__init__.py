"""Signal generators package.

Each generator creates signals from prediction results for a specific market.
"""

from app.signals.generators.btts import BTTSSignalGenerator
from app.signals.generators.handicap import HandicapSignalGenerator
from app.signals.generators.live import LiveSignalGenerator
from app.signals.generators.over_under import OverUnderSignalGenerator
from app.signals.generators.value import ValueSignalGenerator
from app.signals.generators.winner import WinnerSignalGenerator

ALL_GENERATORS = [
    WinnerSignalGenerator,
    OverUnderSignalGenerator,
    BTTSSignalGenerator,
    HandicapSignalGenerator,
    ValueSignalGenerator,
    LiveSignalGenerator,
]

__all__ = [
    "ALL_GENERATORS",
    "WinnerSignalGenerator",
    "OverUnderSignalGenerator",
    "BTTSSignalGenerator",
    "HandicapSignalGenerator",
    "ValueSignalGenerator",
    "LiveSignalGenerator",
]
