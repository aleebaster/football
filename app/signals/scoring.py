"""Signal Scoring — calculates comprehensive signal quality scores."""

from datetime import UTC, datetime

from app.logging import get_logger
from app.prediction.models import PredictionResult
from app.signals.models import Signal, SignalScore, ValueCategory

logger = get_logger(__name__)

# Weights for overall score calculation
SCORE_WEIGHTS = {
    "confidence": 0.25,
    "expected_value": 0.20,
    "data_quality": 0.15,
    "provider_quality": 0.10,
    "prediction_stability": 0.10,
    "historical_accuracy": 0.10,
    "market_quality": 0.10,
}

# Minimum thresholds
MIN_EDGE = 0.02
MIN_CONFIDENCE = 0.4
STRONG_VALUE_THRESHOLD = 0.08
VALUE_THRESHOLD = 0.03


class SignalScorer:
    """Calculates comprehensive signal quality scores."""

    def calculate_score(
        self,
        signal: Signal,
        prediction: PredictionResult | None = None,
        historical_accuracy: float = 0.5,
    ) -> SignalScore:
        """Calculate comprehensive signal score."""
        confidence = signal.confidence
        expected_value = signal.score.expected_value if signal.score else 0.0
        risk = signal.risk_score
        data_quality = (
            prediction.overall_risk.data_completeness
            if prediction and prediction.overall_risk
            else 0.5
        )
        provider_quality = (
            prediction.overall_risk.provider_reliability
            if prediction and prediction.overall_risk
            else 0.5
        )
        prediction_stability = (
            prediction.overall_risk.stability
            if prediction and prediction.overall_risk
            else 0.5
        )
        market_quality = self._assess_market_quality(signal)
        signal_freshness = self._assess_freshness(signal.created_at)

        # Calculate weighted overall score
        overall = self._weighted_overall(
            confidence=confidence,
            expected_value=expected_value,
            data_quality=data_quality,
            provider_quality=provider_quality,
            prediction_stability=prediction_stability,
            historical_accuracy=historical_accuracy,
            market_quality=market_quality,
        )

        factors = self._identify_factors(
            confidence=confidence,
            expected_value=expected_value,
            risk=risk,
            data_quality=data_quality,
        )

        return SignalScore(
            overall=round(overall, 3),
            confidence=round(confidence, 3),
            expected_value=round(expected_value, 4),
            risk=round(risk, 3),
            data_quality=round(data_quality, 3),
            provider_quality=round(provider_quality, 3),
            prediction_stability=round(prediction_stability, 3),
            historical_accuracy=round(historical_accuracy, 3),
            market_quality=round(market_quality, 3),
            signal_freshness=round(signal_freshness, 3),
            factors=factors,
        )

    def categorize_value(self, signal: Signal) -> ValueCategory:
        """Categorize signal by expected value."""
        ev = signal.score.expected_value if signal.score else 0.0
        if ev >= STRONG_VALUE_THRESHOLD:
            return ValueCategory.STRONG_VALUE
        if ev >= VALUE_THRESHOLD:
            return ValueCategory.VALUE
        if ev < 0:
            return ValueCategory.NEGATIVE_EV
        return ValueCategory.NEUTRAL

    def _weighted_overall(
        self,
        confidence: float,
        expected_value: float,
        data_quality: float,
        provider_quality: float,
        prediction_stability: float,
        historical_accuracy: float,
        market_quality: float,
    ) -> float:
        """Calculate weighted overall score."""
        # Normalize expected value to 0-1 range (assume max EV of 0.2)
        ev_normalized = min(1.0, max(0.0, (expected_value + 0.1) / 0.3))

        overall = (
            confidence * SCORE_WEIGHTS["confidence"]
            + ev_normalized * SCORE_WEIGHTS["expected_value"]
            + data_quality * SCORE_WEIGHTS["data_quality"]
            + provider_quality * SCORE_WEIGHTS["provider_quality"]
            + prediction_stability * SCORE_WEIGHTS["prediction_stability"]
            + historical_accuracy * SCORE_WEIGHTS["historical_accuracy"]
            + market_quality * SCORE_WEIGHTS["market_quality"]
        )
        return max(0.0, min(1.0, overall))

    def _assess_market_quality(self, signal: Signal) -> float:
        """Assess quality of the market for this signal."""
        # Base quality by market type
        market_quality_map = {
            "match_winner": 0.8,
            "double_chance": 0.85,
            "over_under_25": 0.75,
            "btts": 0.7,
            "asian_handicap": 0.7,
            "corners": 0.5,
            "cards": 0.5,
            "first_goal": 0.6,
            "halftime": 0.65,
        }
        return market_quality_map.get(signal.market.value, 0.5)

    def _assess_freshness(self, created_at: datetime) -> float:
        """Assess signal freshness based on age."""
        now = datetime.now(UTC)
        age_seconds = (now - created_at).total_seconds()
        # Decay over 1 hour
        if age_seconds < 60:
            return 1.0
        if age_seconds < 3600:
            return 1.0 - (age_seconds - 60) / (3600 - 60) * 0.3
        return 0.5

    def _identify_factors(
        self,
        confidence: float,
        expected_value: float,
        risk: float,
        data_quality: float,
    ) -> list[str]:
        """Identify key factors affecting the score."""
        factors = []
        if confidence >= 0.7:
            factors.append("High confidence")
        elif confidence < 0.4:
            factors.append("Low confidence")
        if expected_value > 0.05:
            factors.append("Strong expected value")
        elif expected_value < 0:
            factors.append("Negative expected value")
        if risk < 0.3:
            factors.append("Low risk")
        elif risk > 0.7:
            factors.append("High risk")
        if data_quality >= 0.8:
            factors.append("High data quality")
        elif data_quality < 0.5:
            factors.append("Limited data quality")
        return factors
