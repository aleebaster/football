"""Loguru logging configuration.

Provides centralized logging setup with:
- Rotating log files
- Colored console output
- Error handling
- Startup logging
"""

import sys

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    """Configure Loguru logging for the application.

    Sets up:
    - Console logging with colors
    - File logging with rotation
    - Error handling
    """
    # Remove default handler
    logger.remove()

    # Console handler with colors
    logger.add(
        sys.stderr,
        level=settings.logging.level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File handler with rotation
    log_file = settings.logs_dir / "app.log"
    logger.add(
        str(log_file),
        level=settings.logging.level.upper(),
        format=settings.logging.format,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression=settings.logging.compression,
        encoding="utf-8",
    )

    # Error file handler
    error_file = settings.logs_dir / "error.log"
    logger.add(
        str(error_file),
        level="ERROR",
        format=settings.logging.format,
        rotation="10 MB",
        retention="90 days",
        compression="gz",
        encoding="utf-8",
    )

    # Log application startup
    logger.info("Logging system initialized")
    logger.info(f"Log level: {settings.logging.level}")
    logger.info(f"Log directory: {settings.logs_dir}")


def get_logger(name: str | None = None) -> logger:
    """Get a named logger instance.

    Args:
        name: Logger name (usually module name).

    Returns:
        Configured logger instance.
    """
    if name:
        return logger.bind(name=name)
    return logger
