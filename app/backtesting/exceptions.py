"""Backtesting Exceptions — custom exceptions for the backtesting platform."""


class BacktestError(Exception):
    """Base exception for backtesting errors."""


class BacktestValidationError(BacktestError):
    """Raised when backtest request validation fails."""


class BacktestDatasetError(BacktestError):
    """Raised when dataset loading fails."""


class BacktestRunError(BacktestError):
    """Raised when backtest execution fails."""


class BacktestExportError(BacktestError):
    """Raised when export fails."""


class BacktestPersistenceError(BacktestError):
    """Raised when persistence operations fail."""


class BacktestComparisonError(BacktestError):
    """Raised when comparison fails."""


class BacktestMetricsError(BacktestError):
    """Raised when metrics calculation fails."""
