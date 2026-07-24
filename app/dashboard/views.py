"""Dashboard Views — view layer for the web interface.

Views describe the presentation structure only.
Presenter logic lives in presenters.py.
Statistics aggregation lives in statistics.py.
"""

from __future__ import annotations

# Re-export from presenters for backward compatibility
from app.dashboard.presenters import DashboardPresenter

__all__ = ["DashboardPresenter"]
