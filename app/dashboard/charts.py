"""Dashboard Charts — chart data providers for the web interface.

Provides structured data for charts without requiring a specific JS library.
Uses a ChartProvider abstraction for future flexibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChartDataset:
    """A single dataset for a chart."""

    label: str
    data: list[float] = field(default_factory=list)
    color: str = "#3b82f6"


@dataclass
class ChartData:
    """Chart data structure compatible with most JS charting libraries."""

    labels: list[str] = field(default_factory=list)
    datasets: list[ChartDataset] = field(default_factory=list)


class ChartProvider:
    """Abstract chart data provider.

    Provides structured data that can be consumed by any JS charting library
    (Chart.js, D3, Plotly, etc.) without coupling to a specific implementation.
    """

    @staticmethod
    def roi_chart(
        labels: list[str],
        values: list[float],
    ) -> ChartData:
        """Generate ROI chart data."""
        return ChartData(
            labels=labels,
            datasets=[ChartDataset(label="ROI %", data=values, color="#10b981")],
        )

    @staticmethod
    def yield_chart(
        labels: list[str],
        values: list[float],
    ) -> ChartData:
        """Generate Yield chart data."""
        return ChartData(
            labels=labels,
            datasets=[ChartDataset(label="Yield %", data=values, color="#6366f1")],
        )

    @staticmethod
    def accuracy_chart(
        labels: list[str],
        values: list[float],
    ) -> ChartData:
        """Generate Accuracy chart data."""
        return ChartData(
            labels=labels,
            datasets=[ChartDataset(label="Accuracy %", data=values, color="#f59e0b")],
        )

    @staticmethod
    def win_rate_chart(
        labels: list[str],
        values: list[float],
    ) -> ChartData:
        """Generate Win Rate chart data."""
        return ChartData(
            labels=labels,
            datasets=[ChartDataset(label="Win Rate %", data=values, color="#ef4444")],
        )

    @staticmethod
    def confidence_distribution(
        buckets: list[str],
        counts: list[int],
    ) -> ChartData:
        """Generate confidence distribution chart data."""
        return ChartData(
            labels=buckets,
            datasets=[
                ChartDataset(
                    label="Predictions",
                    data=[float(c) for c in counts],
                    color="#8b5cf6",
                )
            ],
        )

    @staticmethod
    def risk_distribution(
        buckets: list[str],
        counts: list[int],
    ) -> ChartData:
        """Generate risk distribution chart data."""
        return ChartData(
            labels=buckets,
            datasets=[
                ChartDataset(
                    label="Signals", data=[float(c) for c in counts], color="#ec4899"
                )
            ],
        )

    @staticmethod
    def market_comparison(
        markets: list[str],
        win_rates: list[float],
        rois: list[float],
    ) -> ChartData:
        """Generate market comparison chart data with multiple datasets."""
        return ChartData(
            labels=markets,
            datasets=[
                ChartDataset(label="Win Rate %", data=win_rates, color="#10b981"),
                ChartDataset(label="ROI %", data=rois, color="#6366f1"),
            ],
        )

    @staticmethod
    def calibration_chart(
        expected: list[float],
        observed: list[float],
    ) -> ChartData:
        """Generate calibration chart data (expected vs observed)."""
        return ChartData(
            labels=[f"{e:.0%}" for e in expected],
            datasets=[
                ChartDataset(label="Expected", data=expected, color="#94a3b8"),
                ChartDataset(label="Observed", data=observed, color="#3b82f6"),
            ],
        )
