"""Dashboard module for FastAPI web interface.

Modules:
    router.py        — API router for the dashboard root endpoint
    views.py         — Re-exports DashboardPresenter for backward compatibility
    presenters.py    — Transforms DTOs into dashboard-friendly ViewModels
    statistics.py    — Aggregated statistics for the Dashboard view layer
    widgets.py       — Reusable widget components (Pydantic BaseModel)
    charts.py        — Chart data structures and providers (Pydantic BaseModel)
    pages.py         — Page layout compositions (Pydantic BaseModel)

Architecture:
    Pipeline: Application Service → DTO → Presenter → View
    Widgets, Charts, and Pages use Pydantic BaseModel for serialization,
    validation, and consistency with the project-wide convention.
"""

from app.dashboard.router import router

__all__ = ["router"]
