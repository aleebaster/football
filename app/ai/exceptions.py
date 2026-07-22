"""Custom exceptions for the AI Analysis Engine."""


class AIEngineError(Exception):
    """Base exception for AI Engine errors."""

    def __init__(self, message: str, analyzer: str = "") -> None:
        self.analyzer = analyzer
        super().__init__(message)


class FeatureExtractionError(AIEngineError):
    """Raised when feature extraction fails."""


class RuleEvaluationError(AIEngineError):
    """Raised when rule evaluation fails."""


class InsufficientDataError(AIEngineError):
    """Raised when data is insufficient for analysis."""


class ValidationError(AIEngineError):
    """Raised when input validation fails."""


class AnalysisTimeoutError(AIEngineError):
    """Raised when analysis exceeds time limit."""
