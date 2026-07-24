"""Dashboard Statistics — aggregation logic for dashboard statistics.

This module provides helper functions for computing aggregated statistics
that are displayed on the Dashboard. It operates on DTOs only and does
not access engines directly.
"""

from __future__ import annotations

from typing import Any

from app.application.dto.statistics_dto import (
    MarketStatisticsDTO,
    OverallStatisticsDTO,
)


class DashboardStatistics:
    """Aggregated statistics for the Dashboard view layer.

    Works with DTOs from the Application Layer. Does NOT access
    engines or services directly.
    """

    @staticmethod
    def compute_market_summary(
        markets: list[MarketStatisticsDTO],
    ) -> dict[str, Any]:
        """Compute a summary across all market types.

        Returns a dict with aggregate win rates and ROI per market.
        """
        if not markets:
            return {
                "markets": [],
                "best_market": None,
                "worst_market": None,
                "average_roi": 0.0,
            }

        market_data: list[dict[str, str | float | int]] = [
            {
                "market": m.market,
                "win_rate": round(m.win_rate * 100, 2),
                "roi": round(m.roi * 100, 2),
                "total_predictions": m.total_predictions,
            }
            for m in markets
        ]

        best = max(market_data, key=lambda x: float(x["roi"]))
        worst = min(market_data, key=lambda x: float(x["roi"]))
        avg_roi = sum(float(m["roi"]) for m in market_data) / len(market_data)

        return {
            "markets": market_data,
            "best_market": best["market"],
            "worst_market": worst["market"],
            "average_roi": round(avg_roi, 2),
        }

    @staticmethod
    def compute_performance_summary(
        stats: OverallStatisticsDTO,
    ) -> dict[str, Any]:
        """Compute a high-level performance summary from overall statistics.

        Categorizes the system into a performance tier based on key metrics.
        """
        win_rate_pct = stats.win_rate * 100
        roi_pct = stats.roi * 100

        if win_rate_pct >= 60 and roi_pct >= 10:
            tier = "excellent"
        elif win_rate_pct >= 55 and roi_pct >= 5:
            tier = "good"
        elif win_rate_pct >= 50:
            tier = "average"
        else:
            tier = "needs_improvement"

        return {
            "tier": tier,
            "win_rate_pct": round(win_rate_pct, 2),
            "roi_pct": round(roi_pct, 2),
            "brier_score": round(stats.brier_score, 4),
            "calibration_error": round(stats.calibration_error, 4),
            "signal_accuracy_pct": round(stats.signal_accuracy * 100, 2),
            "total_predictions": stats.total_predictions,
            "total_signals": stats.total_signals,
        }

    @staticmethod
    def compute_health_indicator(
        stats: OverallStatisticsDTO,
    ) -> str:
        """Compute a simple health indicator string for dashboard display.

        Returns: 'green', 'yellow', or 'red'.
        """
        if stats.total_predictions == 0:
            return "yellow"

        win_rate = stats.win_rate
        if win_rate >= 0.55 and stats.roi >= 0.05:
            return "green"
        elif win_rate >= 0.45:
            return "yellow"
        else:
            return "red"
