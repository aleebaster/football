"""Logging module using Loguru.

Provides configured logging with rotation, colored output, and error handling.
"""

from app.logging.config import get_logger, setup_logging

__all__ = ["setup_logging", "get_logger"]
