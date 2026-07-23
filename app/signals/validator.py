"""Validator — validates signals before they enter the pipeline."""

from app.logging import get_logger
from app.prediction.models import PredictionResult
from app.signals.exceptions import SignalValidationError
from app.signals.models import Signal

logger = get_logger(__name__)

MIN_CONFIDENCE = 0.1
MIN_PROBABILITY = 0.0
MAX_PROBABILITY = 1.0


class SignalValidator:
    """Validates signals before they enter the pipeline."""

    def validate_prediction(self, prediction: PredictionResult) -> None:
        """Validate that a prediction result is suitable for signal generation.

        Args:
            prediction: Prediction result to validate.

        Raises:
            SignalValidationError: If validation fails.
        """
        if not prediction.predictions:
            raise SignalValidationError(
                f"No predictions for fixture {prediction.fixture_id}"
            )

        if prediction.overall_confidence < MIN_CONFIDENCE:
            raise SignalValidationError(
                f"Overall confidence {prediction.overall_confidence:.2f} "
                f"below minimum {MIN_CONFIDENCE}"
            )

    def validate_signal(self, signal: Signal) -> bool:
        """Validate a signal.

        Args:
            signal: Signal to validate.

        Returns:
            True if valid.

        Raises:
            SignalValidationError: If validation fails.
        """
        if not signal.id:
            raise SignalValidationError("Signal has no ID")

        if signal.fixture_id <= 0:
            raise SignalValidationError(f"Invalid fixture_id: {signal.fixture_id}")

        if not (MIN_PROBABILITY <= signal.probability <= MAX_PROBABILITY):
            raise SignalValidationError(f"Invalid probability: {signal.probability}")

        if not (MIN_CONFIDENCE <= signal.confidence <= MAX_PROBABILITY):
            raise SignalValidationError(f"Invalid confidence: {signal.confidence}")

        if signal.odds < 1.0:
            raise SignalValidationError(f"Invalid odds: {signal.odds}")

        logger.debug(f"Signal {signal.id} validation passed")
        return True
