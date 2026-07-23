# Football Analysis Platform

Football match analysis and prediction platform with AI-powered insights.

## Architecture

### Data Provider Platform

The Provider Layer is a production-ready data abstraction layer that provides a unified interface for fetching football data from multiple sources.

#### Provider Architecture

```
app/providers/
├── __init__.py          # Public API exports
├── base.py              # BaseProvider abstract class + ProviderHealth
├── models.py            # Normalized Pydantic models (Competition, Team, Fixture, etc.)
├── manager.py           # ProviderManager (fallback, failover, health-based routing)
├── registry.py          # ProviderRegistry (auto-registration and discovery)
├── cache.py             # ProviderCache (type-based TTL caching)
├── health.py            # HealthChecker (periodic health monitoring)
├── scheduler.py         # ProviderScheduler (APScheduler-based periodic sync)
├── http_client.py       # HttpClient (httpx + circuit breaker + rate limiter)
├── rate_limit.py        # RateLimiter (token bucket algorithm)
├── retry.py             # CircuitBreaker (fault tolerance pattern)
├── exceptions.py        # Custom exceptions
└── adapters/
    ├── mock_provider.py    # Mock provider for testing/development
    ├── api_football.py     # API-Football adapter
    └── football_data.py    # Football-Data.org adapter
```

#### Provider Lifecycle

Providers are managed through the `ProviderManager` which handles the full lifecycle:

1. **Registration**: Providers are registered via `ProviderRegistry.register()`
2. **Startup**: `ProviderManager.start()` opens HTTP clients for all providers
3. **Runtime**: Requests flow through fallback/failover chains with health-based routing
4. **Shutdown**: `ProviderManager.stop()` gracefully closes all HTTP clients

The lifecycle is integrated into the FastAPI application lifespan in `main.py`.

#### ProviderManager

The `ProviderManager` is the central orchestrator:

- **Fallback**: If the primary provider fails, the next available provider is tried
- **Failover**: All providers are tried in priority order until one succeeds
- **Priority**: Providers are sorted by priority (lower number = higher priority)
- **Health-based routing**: Unhealthy providers are automatically skipped
- **Recovery**: Providers that recover become eligible again

```python
from app.core.dependencies import get_provider_manager

manager = get_provider_manager()  # Singleton instance
competitions = await manager.competitions()
fixtures = await manager.fixtures(competition_id=1)
```

#### Registry

The `ProviderRegistry` manages provider instances:

```python
from app.providers.registry import ProviderRegistry
from app.providers.adapters.mock_provider import MockProvider

registry = ProviderRegistry()
registry.register(MockProvider(priority=100))
provider = registry.get("mock")  # Returns registered provider
```

#### Fallback Behavior

When a request is made:
1. Active providers are sorted by priority (healthy first)
2. Each provider is tried in order
3. If a provider fails, the next one is attempted
4. If all providers fail, `AllProvidersFailedError` is raised
5. Provider health metrics are updated on each attempt

#### Failover Behavior

Unhealthy providers (consecutive failures ≥ 5 or success rate < 70%) are automatically skipped. If all healthy providers fail, unhealthy ones are tried as a last resort.

#### Caching

The `ProviderCache` implements type-based TTL caching:

| Data Type     | TTL       |
|---------------|-----------|
| live          | 30s       |
| fixtures      | 300s      |
| fixture_detail| 60s       |
| standings     | 3600s     |
| teams         | 86400s    |
| competitions  | 86400s    |
| statistics    | 300s      |
| events        | 60s       |
| odds          | 120s      |
| head_to_head  | 7200s     |

All provider methods use a unified caching strategy through `_execute_with_cache()`.

#### Scheduler

The `ProviderScheduler` uses APScheduler for periodic data synchronization:

- Live match updates
- Fixture synchronization
- Standings refresh
- Team data updates

#### Health Monitoring

The `HealthChecker` tracks:
- Response times
- Success/failure rates
- Consecutive failures
- Overall availability status

Providers are classified as:
- **HEALTHY**: Success rate ≥ 95%
- **DEGRADED**: Success rate 70-95%
- **UNHEALTHY**: Success rate < 70% or consecutive failures ≥ 5
- **UNKNOWN**: No requests made yet

#### Rate Limiting

The `RateLimiter` uses a token bucket algorithm to prevent exceeding API rate limits:
- Configurable tokens per second
- Burst capacity
- Automatic waiting when tokens are exhausted

#### Circuit Breaker

The `CircuitBreaker` provides fault tolerance:
- **Closed**: Normal operation
- **Open**: Too many failures, requests blocked
- **Half-open**: Testing if service recovered (after recovery timeout)

#### HTTP/2 Support

The `HttpClient` supports HTTP/2 when the `h2` package is installed. If not available, it falls back to HTTP/1.1 gracefully.

#### How to Add a New Provider

1. Create a new adapter in `app/providers/adapters/`:

```python
from app.providers.base import BaseProvider
from app.providers.models import Competition, Fixture, ProviderStatus

class MyProvider(BaseProvider):
    def __init__(self, api_key: str, priority: int = 50) -> None:
        super().__init__(name="my_provider", api_key=api_key, priority=priority)

    async def check_health(self) -> ProviderStatus:
        # Implement health check
        return ProviderStatus.HEALTHY

    async def competitions(self) -> list[Competition]:
        # Fetch and normalize competition data
        ...

    # Implement all abstract methods...
```

2. Register in `app/core/dependencies.py`:

```python
if settings.provider.my_api_key:
    from app.providers.adapters.my_provider import MyProvider
    registry.register(MyProvider(api_key=settings.provider.my_api_key, priority=50))
```

3. Add configuration in `app/config/settings.py`:

```python
class ProviderSettings(BaseSettings):
    my_api_key: str = Field(default="", description="My API key")
```

#### Dependency Injection

All providers are accessed through the DI system:

```python
from app.core.dependencies import get_provider_manager, get_provider_registry

# Get the singleton provider manager
manager = get_provider_manager()

# Get the registry
registry = get_provider_registry()
```

**Important**: Never create `ProviderManager` or provider instances directly. Always use the DI system.

## Composition Root & DI Container

The application uses a centralized Composition Root pattern implemented in `app/core/container.py`.

### Container Architecture

All services are assembled in a single `Container` class:

```
app/core/
├── container.py      # Composition Root — single source of truth
└── dependencies.py   # Public API — delegates to container
```

### How It Works

1. **Container** creates and manages all singleton service instances
2. **Lazy initialization** — services are created on first access
3. **Type-safe** — all properties return concrete types (no `object` or `Any` casts)
4. **Shared instances** — every engine (AI, Prediction, Signal, Backtesting) shares the same services

```python
from app.core.container import get_container

container = get_container()

# All engines share the same providers, cache, AI, etc.
ai = container.ai_engine
prediction = container.prediction_engine
signal = container.signal_engine
backtest = container.backtest_engine
```

### Dependency Injection Flow

```
Container (Composition Root)
├── CacheManager (MemoryCache)
├── ProviderRegistry
│   ├── MockProvider
│   ├── ApiFootballProvider
│   └── FootballDataProvider
├── ProviderCache
├── ProviderManager
├── AIEngine
├── PredictionEngine
├── SignalEngine
└── BacktestEngine
    ├── BacktestRunner
    │   ├── BacktestDataset
    │   └── BacktestEvaluator
    └── BacktestOrchestrator
```

### Public API

`app/core/dependencies.py` provides backward-compatible factory functions that delegate to the container:

```python
from app.core.dependencies import (
    get_ai_engine,
    get_prediction_engine,
    get_signal_engine,
    get_backtesting_engine,
    get_provider_manager,
)
```

**Important**: Never create engine instances directly. Always use the DI system.

## Backtesting Platform

The Backtesting Platform validates system quality against historical matches.

### Pipeline

```
Historical Matches
→ Provider Layer
→ AI Analysis Engine
→ Prediction Engine
→ Signal Engine
→ Backtesting Engine
→ Metrics
→ Reports
→ Calibration Dataset
```

### Architecture

```
app/backtesting/
├── engine.py          # BacktestEngine — main entry point
├── orchestrator.py    # Coordinates full backtest pipeline
├── runner.py          # Executes backtests across different scopes
├── dataset.py         # Loads historical match data
├── evaluator.py       # Evaluates individual predictions
├── metrics.py         # Calculates aggregate metrics
├── statistics.py      # Statistical analysis (delegates to metrics)
├── reporting.py       # Generates reports (per league/team/market)
├── calibration.py     # Collects calibration data for model training
├── comparison.py      # Compares different engine versions
├── exporter.py        # Export to CSV/JSON
├── persistence.py     # Stores backtest results
├── validator.py       # Validates backtest requests
├── cache.py           # Backtest-specific caching
├── registry.py        # Registry for backtest configurations
├── history.py         # Tracks backtest run history
└── models.py          # Pydantic models
```

### Core Components

| Component | Purpose |
|-----------|---------|
| `BacktestEngine` | Main entry point, all deps injected via constructor |
| `BacktestOrchestrator` | Coordinates the full pipeline |
| `BacktestRunner` | Executes backtests (per match, league, date range) |
| `BacktestDataset` | Loads historical data from providers |
| `BacktestEvaluator` | Evaluates predictions against actual outcomes |
| `BacktestMetricsCalculator` | Calculates aggregate metrics |
| `BacktestStatistics` | Statistical analysis (delegates to MetricsCalculator) |
| `BacktestReporter` | Generates reports per league/team/market/bucket |
| `BacktestCalibration` | Collects calibration data for future model training |
| `BacktestComparison` | Compares different engine versions |

### Backtest Scopes

| Scope | Description |
|-------|-------------|
| `SINGLE_MATCH` | Single fixture by ID |
| `LEAGUE` | All matches in a league |
| `SEASON` | All matches in a season |
| `DATE_RANGE` | Matches within a date range |
| `ALL` | All available matches |

### Metrics

| Metric | Description |
|--------|-------------|
| Win Rate | Percentage of correct predictions |
| ROI | Return on investment |
| Yield | ROI as percentage |
| Brier Score | Probability calibration quality |
| Log Loss | Logarithmic loss of predictions |
| Calibration Error | Expected Calibration Error (ECE) |
| Precision/Recall/F1 | Classification metrics |
| Average Odds | Mean odds across predictions |
| Average Confidence | Mean prediction confidence |
| Average Risk | Mean risk assessment |

### Reports

| Report | Description |
|--------|-------------|
| Summary | Overall backtest results |
| Per League | Statistics grouped by league |
| Per Team | Statistics grouped by team |
| Per Season | Statistics grouped by season |
| Per Market | Statistics grouped by prediction market |
| Per Predictor | Statistics grouped by model version |
| Per Signal Generator | Statistics for signal vs non-signal predictions |
| Per Confidence Bucket | Performance by confidence level |
| Per Risk Bucket | Performance by risk level |

### How to Run a Backtest

```python
from app.core.dependencies import get_backtesting_engine
from app.backtesting.models import BacktestRequest, BacktestScope

engine = get_backtesting_engine()

# Single match backtest
result = await engine.run(
    BacktestRequest(scope=BacktestScope.SINGLE_MATCH, fixture_id=12345)
)

# League backtest
result = await engine.run(
    BacktestRequest(scope=BacktestScope.LEAGUE, league_id=1, max_matches=100)
)

# Date range backtest
result = await engine.run(
    BacktestRequest(
        scope=BacktestScope.DATE_RANGE,
        date_from="2024-01-01",
        date_to="2024-06-30",
    )
)
```

### How to Add a New Metric

1. Add metric fields to `BacktestMetrics` in `app/backtesting/models.py`
2. Calculate in `BacktestMetricsCalculator.calculate()` in `app/backtesting/metrics.py`
3. Include in reports in `BacktestReporter`
4. Add tests in `tests/test_backtesting.py`

### How to Add a New Report

1. Add report method to `BacktestReporter` in `app/backtesting/reporting.py`
2. Call from `BacktestReporter.generate()`
3. Add tests

## Signal Engine

The Signal Engine is the central module for signal generation and management. It evaluates Prediction Results from the Prediction Engine, assessing quality, risk, and value to decide whether to show a prediction to the user.

### Signal Pipeline

```
PredictionResult
→ Validation
→ Signal Generation
→ Filtering
→ Deduplication
→ Cooldown Check
→ Scoring
→ Ranking (multi-factor)
→ User Preferences
→ Notification Decision
→ Signal
```

### Core Components

| Component | Purpose |
|-----------|---------|
| `SignalEngine` | Main entry point, accepts dependencies via DI |
| `SignalOrchestrator` | Coordinates the full pipeline |
| `SignalScorer` | Calculates comprehensive signal quality scores |
| `SignalRanker` | Multi-factor ranking (EV, confidence, risk, etc.) |
| `SignalFilter` | Filters signals by quality criteria |
| `DeduplicationManager` | Prevents duplicate signals |
| `CooldownManager` | Prevents spam and cyclic updates |
| `NotificationEngine` | Decides when to notify users |
| `SignalHistoryStore` | Tracks signal history for backtesting |
| `ROIEngine` | Calculates ROI and yield statistics |
| `PerformanceEngine` | Tracks performance by market type |

### Signal Generators

| Generator | Market | Description |
|-----------|--------|-------------|
| `WinnerSignalGenerator` | MATCH_WINNER | Home/Draw/Away signals |
| `OverUnderSignalGenerator` | OVER_UNDER_25 | Over/Under goals signals |
| `BTTSSignalGenerator` | BTTS | Both Teams To Score signals |
| `HandicapSignalGenerator` | ASIAN_HANDICAP | Asian handicap signals |
| `ValueSignalGenerator` | All markets | Value bet detection |
| `LiveSignalGenerator` | All markets | Live match signals |

### Signal Score

Each signal receives a comprehensive score:
- **Overall**: Weighted composite score (0-1)
- **Confidence**: Prediction confidence (0-1)
- **Expected Value**: Mathematical edge (-1 to 10)
- **Risk**: Risk assessment (0-1)
- **Data Quality**: Input data completeness (0-1)
- **Provider Quality**: Data source reliability (0-1)
- **Prediction Stability**: Model consistency (0-1)
- **Historical Accuracy**: Past performance (0-1)
- **Market Quality**: Market liquidity/reliability (0-1)
- **Signal Freshness**: Time decay factor (0-1)

### Signal Ranking

Signals are ranked using a multi-factor algorithm:
- Overall Score: 30%
- Confidence: 20%
- Expected Value: 25%
- Risk (inverted): 10%
- Historical Accuracy: 10%
- Provider Quality: 5%

### Signal Filtering

Signals are filtered out if:
- Confidence below threshold (default: 0.3)
- Risk above threshold (default: 0.8)
- Data too old (>1 hour)
- No explanation provided
- Signal is inactive

### Value Categories

| Category | EV Range | Description |
|----------|----------|-------------|
| STRONG_VALUE | ≥ 0.08 | High confidence value bet |
| VALUE | ≥ 0.03 | Moderate value |
| NEUTRAL | 0 to 0.03 | No clear edge |
| NEGATIVE_EV | < 0 | Not recommended |

### How to Add a New Signal Generator

1. Create a generator in `app/signals/generators/`:

```python
from app.signals.interfaces import BaseSignalGenerator
from app.prediction.models import PredictionResult
from app.signals.models import Signal

class MySignalGenerator(BaseSignalGenerator):
    async def generate(self, prediction: PredictionResult) -> list[Signal]:
        # Generate signals from prediction
        return [Signal(...)]
```

2. Register in `app/signals/engine.py`:

```python
from app.signals.generators.my_generator import MySignalGenerator

self._registry.register(MySignalGenerator(), PredictionMarket.MY_MARKET)
```

3. Add tests in `tests/test_signals.py`.

### Dependency Injection

The Signal Engine integrates with the DI system:

```python
from app.core.dependencies import get_signal_engine

engine = get_signal_engine()  # Singleton instance
signals = await engine.process(prediction)
```

All components can be injected via the `SignalEngine` constructor:

```python
engine = SignalEngine(
    cache_manager=cache_manager,
    registry=custom_registry,
    validator=custom_validator,
    signal_filter=custom_filter,
    # ... other dependencies
)
```

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main

# Run tests
pytest

# Type checking
mypy .

# Linting
ruff check .
```

### Environment Variables

```env
# Provider API Keys
PROVIDER_API_FOOTBALL_KEY=your_key
PROVIDER_FOOTBALL_DATA_KEY=your_key

# Database
DATABASE_URL=sqlite+aiosqlite:///football.db

# Telegram
TELEGRAM_BOT_TOKEN=your_token
```
