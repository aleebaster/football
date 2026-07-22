"""Prediction Engine exceptions."""


class PredictionError(Exception):
    """Base exception for prediction engine."""


class InsufficientAnalysisError(PredictionError):
    """Raised when analysis result is insufficient for prediction."""


class LowConfidenceError(PredictionError):
    """Raised when confidence is below minimum threshold."""


class ValidationFailedError(PredictionError):
    """Raised when prediction validation fails."""


class MarketNotSupportedError(PredictionError):
    """Raised when requested prediction market is not supported."""
