"""Common utility functions.

Provides helper functions used across the application.
"""

import uuid
from datetime import UTC, datetime
from typing import Any


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID.

    Returns:
        New UUID instance.
    """
    return uuid.uuid4()


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp.

    Returns:
        Current datetime in UTC.
    """
    return datetime.now(UTC)


def format_number(value: float, decimals: int = 2) -> str:
    """Format a number with specified decimal places.

    Args:
        value: Number to format.
        decimals: Number of decimal places.

    Returns:
        Formatted number string.
    """
    return f"{value:.{decimals}f}"


def safe_get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.

    Args:
        data: Dictionary to search.
        *keys: Keys to traverse.
        default: Default value if not found.

    Returns:
        Nested value or default.
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def chunk_list(lst: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks.

    Args:
        lst: List to split.
        chunk_size: Size of each chunk.

    Returns:
        List of chunks.
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]
