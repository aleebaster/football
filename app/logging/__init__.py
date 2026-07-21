"""Logging module using Loguru.

Provides configured logging with rotation, colored output, and error handling.
"""

from app.logging.config import setup_logging

__all__ = ["setup_logging"]
