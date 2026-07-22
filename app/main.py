"""Main application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.core.dependencies import (
    get_cache_manager,
    get_provider_manager,
    register_default_providers,
)
from app.database.session import db_manager
from app.logging import get_logger
from app.logging.config import setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    setup_logging()
    logger.info("Starting application...")

    await db_manager.connect()
    logger.info("Database connected")

    get_cache_manager()
    logger.info("Cache initialized")

    await db_manager.create_tables()
    logger.info("Database tables created")

    # Initialize provider platform
    provider_manager = None
    try:
        register_default_providers()
        provider_manager = get_provider_manager()
        await provider_manager.start()
        if provider_manager.degraded:
            logger.warning(
                f"Application started in DEGRADED MODE: {provider_manager.degraded_reason}"
            )
        else:
            logger.info("Provider platform started")
    except Exception as e:
        logger.error(f"Failed to start provider platform: {e}")

    logger.info("Application started successfully")

    yield

    logger.info("Shutting down application...")

    # Stop provider platform
    if provider_manager is not None:
        await provider_manager.stop()
        logger.info("Provider platform stopped")

    await db_manager.disconnect()
    logger.info("Database disconnected")
    logger.info("Application shut down successfully")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.project_name,
        description="Football match analysis and prediction platform",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    from app.dashboard import router

    application.include_router(router)

    return application


app = create_app()


def run_server() -> None:
    """Run the application server."""
    uvicorn.run(
        "app.main:app",
        host=settings.dashboard.host,
        port=settings.dashboard.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run_server()
