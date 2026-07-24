"""Main application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    # Initialize Live Engine
    live_engine = None
    try:
        from app.core.container import get_container

        container = get_container()
        live_engine = container.live_engine
        await live_engine.start()
        logger.info("Live Engine started")
    except Exception as e:
        logger.error(f"Failed to start Live Engine: {e}")

    logger.info("Application started successfully")

    yield

    logger.info("Shutting down application...")

    # Stop Live Engine
    if live_engine is not None:
        await live_engine.stop()
        logger.info("Live Engine stopped")

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

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    from app.api.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)

    # Dashboard root router
    from app.dashboard import router

    application.include_router(router)

    # API routers
    from app.api.routers import (
        backtesting_router,
        configuration_router,
        health_router,
        live_router,
        matches_router,
        predictions_router,
        providers_router,
        signals_router,
        statistics_router,
    )

    application.include_router(health_router, tags=["Health"])
    application.include_router(matches_router, tags=["Matches"])
    application.include_router(predictions_router, tags=["Predictions"])
    application.include_router(signals_router, tags=["Signals"])
    application.include_router(backtesting_router, tags=["Backtesting"])
    application.include_router(statistics_router, tags=["Statistics"])
    application.include_router(providers_router, tags=["Providers"])
    application.include_router(configuration_router, tags=["Configuration"])
    application.include_router(live_router, tags=["Live"])

    # Live Dashboard endpoints
    from app.api.routers import live_dashboard_router

    application.include_router(live_dashboard_router, tags=["Live Dashboard"])

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
