"""Dashboard Pages — page layouts for the web interface.

Each page aggregates widgets and charts into a coherent view.
Pages do not contain business logic — they compose widgets from the Application Layer.

Architecture decision: Pydantic BaseModel is used instead of dataclass to ensure
automatic JSON serialization, field validation, and consistency with the
project-wide convention where all serializable models use Pydantic.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.dashboard.charts import ChartData
from app.dashboard.widgets import Widget


class DashboardPage(BaseModel):
    """A dashboard page layout."""

    title: str
    description: str = ""
    widgets: list[Widget] = Field(default_factory=list)
    charts: list[ChartData] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)


class PageFactory:
    """Creates dashboard pages from Application Layer data."""

    @staticmethod
    def overview_page(
        widgets: list[Widget],
        charts: list[ChartData] | None = None,
    ) -> DashboardPage:
        return DashboardPage(
            title="Overview",
            description="System overview and key metrics",
            widgets=widgets,
            charts=charts or [],
        )

    @staticmethod
    def providers_page(
        widgets: list[Widget],
    ) -> DashboardPage:
        return DashboardPage(
            title="Providers",
            description="Data provider health and status",
            widgets=widgets,
        )

    @staticmethod
    def predictions_page(
        widgets: list[Widget],
        charts: list[ChartData] | None = None,
    ) -> DashboardPage:
        return DashboardPage(
            title="Predictions",
            description="Prediction summaries and market breakdowns",
            widgets=widgets,
            charts=charts or [],
        )

    @staticmethod
    def signals_page(
        widgets: list[Widget],
    ) -> DashboardPage:
        return DashboardPage(
            title="Signals",
            description="Active signals and signal history",
            widgets=widgets,
        )

    @staticmethod
    def backtesting_page(
        widgets: list[Widget],
        charts: list[ChartData] | None = None,
    ) -> DashboardPage:
        return DashboardPage(
            title="Backtesting",
            description="Backtest results and performance analysis",
            widgets=widgets,
            charts=charts or [],
        )

    @staticmethod
    def statistics_page(
        widgets: list[Widget],
        charts: list[ChartData] | None = None,
    ) -> DashboardPage:
        return DashboardPage(
            title="Statistics",
            description="Overall performance statistics",
            widgets=widgets,
            charts=charts or [],
        )

    @staticmethod
    def health_page(
        widgets: list[Widget],
    ) -> DashboardPage:
        return DashboardPage(
            title="Health",
            description="System health status",
            widgets=widgets,
        )

    @staticmethod
    def configuration_page(
        widgets: list[Widget],
    ) -> DashboardPage:
        return DashboardPage(
            title="Configuration",
            description="Application configuration",
            widgets=widgets,
        )
