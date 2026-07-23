"""Dashboard Widgets — reusable widget components for the web interface.

Widgets are small, composable UI components that display data from the Application Layer.
They do not contain business logic — only presentation formatting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Widget:
    """Base widget structure."""

    title: str
    value: str | int | float = ""
    subtitle: str = ""
    icon: str = ""
    color: str = "blue"
    metadata: dict[str, Any] = field(default_factory=dict)


class WidgetFactory:
    """Creates dashboard widgets from DTOs."""

    @staticmethod
    def stat_widget(
        title: str,
        value: str | int | float,
        subtitle: str = "",
        icon: str = "",
        color: str = "blue",
    ) -> Widget:
        return Widget(
            title=title,
            value=value,
            subtitle=subtitle,
            icon=icon,
            color=color,
        )

    @staticmethod
    def health_widget(
        name: str,
        status: str,
        details: str = "",
    ) -> Widget:
        color_map = {
            "healthy": "green",
            "degraded": "yellow",
            "unhealthy": "red",
            "unknown": "gray",
        }
        return Widget(
            title=name,
            value=status,
            subtitle=details,
            icon="heart" if status == "healthy" else "alert",
            color=color_map.get(status, "gray"),
        )

    @staticmethod
    def provider_widget(
        name: str,
        status: str,
        success_rate: float,
        avg_ms: float,
    ) -> Widget:
        return Widget(
            title=name,
            value=f"{success_rate:.1f}%",
            subtitle=f"{avg_ms:.0f}ms avg",
            icon="server",
            color="green" if status == "healthy" else "red",
        )

    @staticmethod
    def overview_widgets(
        total_predictions: int,
        total_signals: int,
        win_rate: float,
        roi: float,
    ) -> list[Widget]:
        return [
            Widget(
                title="Predictions", value=total_predictions, icon="chart", color="blue"
            ),
            Widget(title="Signals", value=total_signals, icon="bell", color="purple"),
            Widget(
                title="Win Rate", value=f"{win_rate:.1f}%", icon="trophy", color="green"
            ),
            Widget(
                title="ROI", value=f"{roi:.2f}%", icon="trending-up", color="emerald"
            ),
        ]
