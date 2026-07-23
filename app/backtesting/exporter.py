"""Backtesting Exporter — exports backtest results to CSV/JSON."""

import csv
import json
from pathlib import Path

from app.backtesting.exceptions import BacktestExportError
from app.backtesting.models import BacktestResult, ExportFormat
from app.logging import get_logger

logger = get_logger(__name__)


class BacktestExporter:
    """Exports backtest results to various formats."""

    async def export(
        self,
        result: BacktestResult,
        path: str,
        fmt: ExportFormat = ExportFormat.JSON,
    ) -> str:
        """Export backtest results to a file.

        Args:
            result: Backtest result to export.
            path: Output file path.
            fmt: Export format.

        Returns:
            Path to the exported file.

        Raises:
            BacktestExportError: If export fails.
        """
        try:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if fmt == ExportFormat.JSON:
                return await self._export_json(result, output_path)
            elif fmt == ExportFormat.CSV:
                return await self._export_csv(result, output_path)
            else:
                raise BacktestExportError(f"Unsupported format: {fmt}")

        except BacktestExportError:
            raise
        except Exception as e:
            raise BacktestExportError(f"Export failed: {e}") from e

    async def _export_json(self, result: BacktestResult, path: Path) -> str:
        """Export to JSON format."""
        data = {
            "id": result.id,
            "status": result.status.value,
            "ai_version": result.ai_version,
            "prediction_version": result.prediction_version,
            "signal_version": result.signal_version,
            "metrics": result.metrics.model_dump(mode="json"),
            "total_evaluations": len(result.evaluations),
            "evaluations": [e.model_dump(mode="json") for e in result.evaluations],
            "started_at": result.started_at.isoformat(),
            "completed_at": (
                result.completed_at.isoformat() if result.completed_at else None
            ),
            "duration_seconds": result.duration_seconds,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported to JSON: {path}")
        return str(path)

    async def _export_csv(self, result: BacktestResult, path: Path) -> str:
        """Export evaluations to CSV format."""
        if not result.evaluations:
            logger.warning("No evaluations to export")
            return str(path)

        fieldnames = [
            "fixture_id",
            "market",
            "predicted_outcome",
            "predicted_probability",
            "actual_outcome",
            "is_correct",
            "odds",
            "stake",
            "pnl",
            "roi",
            "edge",
            "expected_value",
            "confidence",
            "risk_score",
            "model_version",
        ]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for eval_result in result.evaluations:
                writer.writerow(
                    {
                        "fixture_id": eval_result.fixture_id,
                        "market": eval_result.market,
                        "predicted_outcome": eval_result.predicted_outcome,
                        "predicted_probability": eval_result.predicted_probability,
                        "actual_outcome": eval_result.actual_outcome,
                        "is_correct": eval_result.is_correct,
                        "odds": eval_result.odds,
                        "stake": eval_result.stake,
                        "pnl": eval_result.pnl,
                        "roi": eval_result.roi,
                        "edge": eval_result.edge,
                        "expected_value": eval_result.expected_value,
                        "confidence": eval_result.confidence,
                        "risk_score": eval_result.risk_score,
                        "model_version": eval_result.model_version,
                    }
                )

        logger.info(f"Exported to CSV: {path}")
        return str(path)
