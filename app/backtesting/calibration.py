"""Backtesting Calibration — collects data for model calibration training."""

from app.backtesting.models import (
    BacktestResult,
    CalibrationDataset,
)
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestCalibration:
    """Collects calibration data from backtest results."""

    def __init__(self) -> None:
        self._datasets: list[CalibrationDataset] = []

    async def collect(
        self,
        result: BacktestResult,
    ) -> list[CalibrationDataset]:
        """Collect calibration data from a backtest result.

        Args:
            result: Backtest result to extract calibration data from.

        Returns:
            List of calibration dataset entries.
        """
        calibration_entries: list[CalibrationDataset] = []

        for evaluation in result.evaluations:
            entry = CalibrationDataset(
                fixture_id=evaluation.fixture_id,
                market=evaluation.market,
                predicted_probability=evaluation.predicted_probability,
                actual_outcome=evaluation.is_correct,
                odds=evaluation.odds,
                confidence=evaluation.confidence,
                model_version=evaluation.model_version,
            )
            calibration_entries.append(entry)

        self._datasets.extend(calibration_entries)
        logger.info(
            f"Collected {len(calibration_entries)} calibration entries "
            f"(total: {len(self._datasets)})"
        )
        return calibration_entries

    def get_all(self) -> list[CalibrationDataset]:
        """Get all collected calibration data.

        Returns:
            List of all calibration dataset entries.
        """
        return list(self._datasets)

    def get_by_market(self, market: str) -> list[CalibrationDataset]:
        """Get calibration data filtered by market.

        Args:
            market: Market type to filter by.

        Returns:
            Filtered calibration entries.
        """
        return [d for d in self._datasets if d.market == market]

    def get_by_version(self, version: str) -> list[CalibrationDataset]:
        """Get calibration data filtered by model version.

        Args:
            version: Model version to filter by.

        Returns:
            Filtered calibration entries.
        """
        return [d for d in self._datasets if d.model_version == version]

    def clear(self) -> None:
        """Clear all collected calibration data."""
        self._datasets.clear()
        logger.info("Cleared calibration dataset")

    def __len__(self) -> int:
        return len(self._datasets)
