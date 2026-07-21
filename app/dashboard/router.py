"""Dashboard API router.

Provides health check and status endpoints.
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


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status.
    """
    return {"status": "healthy"}


@router.get("/status")
async def status() -> dict[str, str | bool]:
    """Application status endpoint.

    Returns:
        Application status information.
    """
    return {
        "status": "running",
        "debug": settings.debug,
        "language": settings.language,
    }
