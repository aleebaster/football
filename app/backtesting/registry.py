"""Backtesting Registry — manages backtest configurations and plugins."""

from app.logging import get_logger

logger = get_logger(__name__)


class BacktestRegistry:
    """Registry for backtest configurations and custom plugins."""

    def __init__(self) -> None:
        self._configs: dict[str, dict[str, object]] = {}

    def register(self, name: str, config: dict[str, object]) -> None:
        """Register a backtest configuration.

        Args:
            name: Configuration name.
            config: Configuration dictionary.
        """
        self._configs[name] = config
        logger.debug(f"Registered backtest config: {name}")

    def get(self, name: str) -> dict[str, object] | None:
        """Get a registered configuration.

        Args:
            name: Configuration name.

        Returns:
            Configuration dictionary or None.
        """
        return self._configs.get(name)

    def get_all(self) -> dict[str, dict[str, object]]:
        """Get all registered configurations.

        Returns:
            Dictionary of all configurations.
        """
        return dict(self._configs)

    def unregister(self, name: str) -> bool:
        """Unregister a configuration.

        Args:
            name: Configuration name.

        Returns:
            True if unregistered.
        """
        if name in self._configs:
            del self._configs[name]
            return True
        return False

    def __len__(self) -> int:
        return len(self._configs)

    def __contains__(self, name: str) -> bool:
        return name in self._configs
