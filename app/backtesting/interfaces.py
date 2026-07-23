"""Backtesting Interfaces — abstract base classes for the backtesting platform."""

from abc import ABC, abstractmethod
from typing import Any

from app.backtesting.models import (
    BacktestRequest,
    BacktestResult,
    BacktestSummary,
    EvaluationResult,
)


class BaseBacktestDataset(ABC):
    """Abstract base class for backtest datasets."""

    @abstractmethod
    async def load(self, request: BacktestRequest) -> list[dict[str, Any]]:
        """Load historical match data for backtesting."""
        ...

    @abstractmethod
    async def get_match(self, fixture_id: int) -> dict[str, Any] | None:
        """Get a specific historical match."""
        ...

    @abstractmethod
    async def count(self, request: BacktestRequest) -> int:
        """Count matches in the dataset."""
        ...


class BaseBacktestEvaluator(ABC):
    """Abstract base class for backtest evaluation."""

    @abstractmethod
    async def evaluate(self, prediction: Any, actual_outcome: str) -> EvaluationResult:
        """Evaluate a single prediction against actual outcome."""
        ...


class BaseBacktestMetrics(ABC):
    """Abstract base class for backtest metrics calculation."""

    @abstractmethod
    async def calculate(self, results: list[EvaluationResult]) -> dict[str, Any]:
        """Calculate aggregate metrics from evaluation results."""
        ...


class BaseBacktestReporter(ABC):
    """Abstract base class for backtest reporting."""

    @abstractmethod
    async def generate(self, result: BacktestResult) -> BacktestSummary:
        """Generate a summary report from backtest results."""
        ...


class BaseBacktestExporter(ABC):
    """Abstract base class for backtest data export."""

    @abstractmethod
    async def export(self, result: BacktestResult, path: str) -> str:
        """Export backtest results to a file."""
        ...
