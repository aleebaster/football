"""Loguru logging configuration."""

import sys
from typing import Any

from loguru import logger as _logger

from app.config import settings


def setup_logging() -> None:
    """Configure Loguru logging for the application."""
    _logger.remove()

    _logger.add(
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

    log_file = settings.logs_dir / "app.log"
    _logger.add(
        str(log_file),
        level=settings.logging.level.upper(),
        format=settings.logging.format,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression=settings.logging.compression,
        encoding="utf-8",
    )

    error_file = settings.logs_dir / "error.log"
    _logger.add(
        str(error_file),
        level="ERROR",
        format=settings.logging.format,
        rotation="10 MB",
        retention="90 days",
        compression="gz",
        encoding="utf-8",
    )

    _logger.info("Logging system initialized")
    _logger.info(f"Log level: {settings.logging.level}")
    _logger.info(f"Log directory: {settings.logs_dir}")


def get_logger(name: str | None = None) -> Any:
    """Get a named logger instance."""
    if name:
        return _logger.bind(name=name)
    return _logger
