"""Signal Engine — central module for signal generation and management.

Pipeline:
    Provider Layer → AI Engine → Prediction Engine → Signal Engine → Telegram / Dashboard

The Signal Engine takes PredictionResult, evaluates quality, risk, and value,
then decides whether to show a prediction to the user, when to send it,
to whom, with what priority, when to update, and when to recall it.
"""

from app.signals.engine import SignalEngine
from app.signals.exceptions import (
    SignalCooldownError,
    SignalDuplicateError,
    SignalError,
    SignalFilterError,
    SignalNotFoundError,
    SignalValidationError,
)
from app.signals.models import (
    PerformanceStatistics,
    Portfolio,
    ROIStatistics,
    Signal,
    SignalHistory,
    SignalMetrics,
    SignalNotification,
    SignalRequest,
    SignalScore,
    SignalStatus,
    SignalType,
    UserPreferences,
    ValueCategory,
    Watchlist,
)

__all__ = [
    "SignalEngine",
    "Signal",
    "SignalRequest",
    "SignalScore",
    "SignalHistory",
    "SignalNotification",
    "SignalMetrics",
    "SignalType",
    "SignalStatus",
    "ValueCategory",
    "UserPreferences",
    "Watchlist",
    "Portfolio",
    "ROIStatistics",
    "PerformanceStatistics",
    "SignalError",
    "SignalValidationError",
    "SignalFilterError",
    "SignalDuplicateError",
    "SignalCooldownError",
    "SignalNotFoundError",
]
