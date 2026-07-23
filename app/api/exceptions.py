"""API Exceptions — custom exception handlers for FastAPI."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.logging import get_logger

logger = get_logger(__name__)


class APINotFoundError(HTTPException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=404, detail=detail)


class APIValidationError(HTTPException):
    """Validation error."""

    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(status_code=422, detail=detail)


class APIServiceUnavailableError(HTTPException):
    """Service temporarily unavailable."""

    def __init__(self, detail: str = "Service temporarily unavailable") -> None:
        super().__init__(status_code=503, detail=detail)


class APIInternalError(HTTPException):
    """Internal server error."""

    def __init__(self, detail: str = "Internal server error") -> None:
        super().__init__(status_code=500, detail=detail)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP exception handler with structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
