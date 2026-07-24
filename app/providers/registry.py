"""Provider registry for auto-registration and discovery."""

from app.logging import get_logger
from app.providers.base import BaseProvider
from app.providers.exceptions import ProviderNotFoundError

logger = get_logger(__name__)


class ProviderRegistry:
    """Registry for managing provider instances."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        self._providers[provider.name] = provider
        logger.info(f"Registered provider: {provider.name}")

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)
        logger.info(f"Unregistered provider: {name}")

    def get(self, name: str) -> BaseProvider:
        if name not in self._providers:
            raise ProviderNotFoundError(f"Provider '{name}' not found", provider=name)
        return self._providers[name]

    def get_all(self) -> list[BaseProvider]:
        return sorted(self._providers.values(), key=lambda p: p.priority)

    def get_enabled(self) -> list[BaseProvider]:
        return [p for p in self.get_all() if p.enabled]

    def names(self) -> list[str]:
        return list(self._providers.keys())

    def items(self) -> list[tuple[str, BaseProvider]]:
        """Return (name, provider) pairs for iteration."""
        return list(self._providers.items())

    def values(self) -> list[BaseProvider]:
        """Return all registered providers."""
        return list(self._providers.values())

    def __contains__(self, name: str) -> bool:
        return name in self._providers

    def __len__(self) -> int:
        return len(self._providers)

    def __repr__(self) -> str:
        return f"<ProviderRegistry(providers={list(self._providers.keys())})>"
