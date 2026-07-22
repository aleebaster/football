"""Validator — validates analysis results before generating predictions."""

from app.ai.models import AnalysisResult, AnalysisStatus
from app.logging import get_logger
from app.prediction.exceptions import InsufficientAnalysisError, LowConfidenceError

logger = get_logger(__name__)

MIN_FEATURES = 3
MIN_CONFIDENCE = 0.1


class PredictionValidator:
    """Validates that analysis result is sufficient for prediction."""

    def validate(self, analysis: AnalysisResult) -> None:
        """Validate analysis result. Raises on failure."""
        if analysis.status == AnalysisStatus.FAILED:
            raise InsufficientAnalysisError(
                f"Analysis failed for fixture {analysis.fixture_id}"
            )

        if analysis.features is None:
            raise InsufficientAnalysisError("No features available")

        if len(analysis.features.features) < MIN_FEATURES:
            raise InsufficientAnalysisError(
                f"Insufficient features: {len(analysis.features.features)} < {MIN_FEATURES}"
            )

        if analysis.confidence and analysis.confidence.overall < MIN_CONFIDENCE:
            raise LowConfidenceError(
                f"Confidence {analysis.confidence.overall:.2f} below threshold {MIN_CONFIDENCE}"
            )

        logger.debug(f"Validation passed for fixture {analysis.fixture_id}")
