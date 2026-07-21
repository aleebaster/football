"""Main application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.core.dependencies import get_cache_manager
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

    logger.info("Application started successfully")

    yield

    logger.info("Shutting down application...")
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
