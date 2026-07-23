"""Value Signal Generator — generates signals specifically for value bets."""

import uuid

from app.logging import get_logger
from app.prediction.models import PredictionResult
from app.signals.interfaces import BaseSignalGenerator
from app.signals.models import (
    Signal,
    SignalPriority,
    SignalType,
    ValueCategory,
)

logger = get_logger(__name__)

STRONG_VALUE_EDGE = 0.08
VALUE_EDGE = 0.03


class ValueSignalGenerator(BaseSignalGenerator):
    """Generates signals specifically for value bets across all markets."""

    async def generate(self, prediction: PredictionResult) -> list[Signal]:
        """Generate value signals from all value bets in prediction."""
        signals: list[Signal] = []

        for pred in prediction.predictions:
            for vb in pred.value_bets:
                if vb.edge < VALUE_EDGE:
                    continue

                value_cat = (
                    ValueCategory.STRONG_VALUE
                    if vb.edge >= STRONG_VALUE_EDGE
                    else ValueCategory.VALUE
                )
                priority = (
                    SignalPriority.CRITICAL
                    if vb.edge >= STRONG_VALUE_EDGE
                    else SignalPriority.HIGH
                )

                signal = Signal(
                    id=f"sig_{uuid.uuid4().hex[:12]}",
                    fixture_id=prediction.fixture_id,
                    home_team_id=prediction.home_team_id,
                    away_team_id=prediction.away_team_id,
                    signal_type=SignalType.NEW,
                    priority=priority,
                    market=vb.market,
                    prediction_id=f"pred_{prediction.fixture_id}",
                    outcome=vb.outcome,
                    probability=round(vb.model_probability, 4),
                    confidence=round(pred.confidence, 4),
                    odds=round(vb.market_odds, 2),
                    value_category=value_cat,
                    risk_level=prediction.overall_risk.level,
                    risk_score=prediction.overall_risk.score,
                    summary=vb.explanation
                    or f"Value on {vb.outcome}: edge {vb.edge:.1%}",
                    key_factors=[
                        f"Market: {vb.market.value}",
                        f"Edge: {vb.edge:.1%}",
                        f"EV: {vb.expected_value:.1%}",
                        f"Kelly: {vb.kelly.fraction:.1%}",
                    ],
                    model_version=prediction.model_version,
                )
                signals.append(signal)

        logger.debug(
            f"Generated {len(signals)} value signals for fixture {prediction.fixture_id}"
        )
        return signals
