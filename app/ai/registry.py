"""Registry for AI analyzers."""

from app.ai.interfaces import BaseAnalyzer
from app.logging import get_logger

logger = get_logger(__name__)


class AnalyzerRegistry:
    """Registry that manages all available analyzers."""

    def __init__(self) -> None:
        self._analyzers: dict[str, BaseAnalyzer] = {}

    def register(self, analyzer: BaseAnalyzer) -> None:
        self._analyzers[analyzer.name] = analyzer
        logger.debug(f"Registered analyzer: {analyzer.name}")

    def get(self, name: str) -> BaseAnalyzer | None:
        return self._analyzers.get(name)

    def get_all(self) -> list[BaseAnalyzer]:
        return list(self._analyzers.values())

    def get_by_names(self, names: list[str]) -> list[BaseAnalyzer]:
        return [a for a in self._analyzers.values() if a.name in names]

    def __len__(self) -> int:
        return len(self._analyzers)

    def __contains__(self, name: str) -> bool:
        return name in self._analyzers
