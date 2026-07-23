"""Dashboard API router.

Provides the root endpoint and health check.
All API routers are mounted from main.py.
"""

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Welcome message with project info.
    """
    return {
        "message": f"Welcome to {settings.project_name}",
        "version": "0.1.0",
    }
