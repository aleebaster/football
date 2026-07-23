"""Backtesting Platform — Production-ready backtesting module.

Pipeline:
    Historical Matches → Provider Layer → AI Engine → Prediction Engine →
    Signal Engine → Backtesting Engine → Metrics → Reports → Calibration Dataset

The backtesting platform reuses all existing engines without duplicating logic.
All services are assembled through the Composition Root (app/core/container.py).
"""

from app.backtesting.calibration import BacktestCalibration
from app.backtesting.comparison import BacktestComparison
from app.backtesting.engine import BacktestEngine
from app.backtesting.exceptions import (
    BacktestComparisonError,
    BacktestDatasetError,
    BacktestError,
    BacktestExportError,
    BacktestMetricsError,
    BacktestPersistenceError,
    BacktestRunError,
    BacktestValidationError,
)
from app.backtesting.exporter import BacktestExporter
from app.backtesting.models import (
    BacktestMetrics,
    BacktestRequest,
    BacktestResult,
    BacktestScope,
    BacktestStatus,
    BacktestSummary,
    CalibrationDataset,
    ComparisonResult,
    EvaluationResult,
    ExportFormat,
    LeagueStatistics,
    MarketBreakdown,
    PredictionStatistics,
    SeasonStatistics,
    SignalStatistics,
    TeamStatistics,
)

__all__ = [
    "BacktestEngine",
    "BacktestRequest",
    "BacktestResult",
    "BacktestSummary",
    "BacktestMetrics",
    "BacktestStatus",
    "BacktestScope",
    "EvaluationResult",
    "ComparisonResult",
    "CalibrationDataset",
    "MarketBreakdown",
    "ExportFormat",
    "LeagueStatistics",
    "SeasonStatistics",
    "TeamStatistics",
    "PredictionStatistics",
    "SignalStatistics",
    "BacktestCalibration",
    "BacktestComparison",
    "BacktestExporter",
    "BacktestError",
    "BacktestValidationError",
    "BacktestDatasetError",
    "BacktestRunError",
    "BacktestExportError",
    "BacktestPersistenceError",
    "BacktestComparisonError",
    "BacktestMetricsError",
]
