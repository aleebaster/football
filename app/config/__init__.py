"""Configuration module for the application.

Provides centralized configuration management using Pydantic Settings.
All configuration is loaded from environment variables and .env files.
"""

from app.config.settings import settings

__all__ = ["settings"]
