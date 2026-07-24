# Football Analysis Platform

Football match analysis and prediction platform with AI-powered insights.

## Architecture Overview

```
REST API / Dashboard / CLI / Telegram
        ↓
Application Layer (Services + DTOs + Mapper)
        ↓
Engine Layer (AI, Prediction, Signal, Backtesting)
        ↓
Provider Layer (Multi-source data abstraction)
```

## REST API

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root endpoint (welcome message) |
| GET | `/health` | System health status (providers, engines, cache) |
| GET | `/matches` | List matches with optional `competition_id` and `limit` |
| GET | `/matches/{fixture_id}` | Get a single match by ID |
| GET | `/predictions/{fixture_id}` | Full prediction for a fixture |
| GET | `/predictions/{fixture_id}/summary` | Prediction summary (win/draw/away probabilities) |
| GET | `/signals` | Paginated signal list (`page`, `page_size`) |
| GET | `/signals/{signal_id}` | Single signal by ID |
| GET | `/backtests` | List recent backtests (`limit`) |
| GET | `/backtests/{backtest_id}` | Single backtest result |
| POST | `/backtests/run` | Run a new backtest (body: fixture_id, league_id, date_from, date_to, max_matches) |
| GET | `/statistics` | Overall statistics (win_rate, ROI, yield, Brier score, etc.) |
| GET | `/statistics/roi` | ROI statistics (aggregated alias of `/statistics`) |
| GET | `/statistics/yield` | Yield statistics (aggregated alias of `/statistics`) |
| GET | `/statistics/winrate` | Win rate statistics (aggregated alias of `/statistics`) |
| GET | `/statistics/markets` | Statistics broken down by market type |
| GET | `/statistics/leagues` | Statistics broken down by league |
| GET | `/statistics/teams` | Statistics broken down by team (placeholder) |
| GET | `/providers` | Provider health and status |
| GET | `/configuration` | Application configuration |
| GET | `/live` | Live engine status |
| GET | `/live/matches` | Active live matches |
| GET | `/live/workers` | Worker information |
| GET | `/live/events` | Recent live events |
| GET | `/live/metrics` | Live engine metrics |
| GET | `/live/heartbeat` | Heartbeat information |
| GET | `/live/state` | Current match states |

### Request/Response

All responses use Pydantic models for automatic validation and serialization.
Pagination is supported via `page` and `page_size` query parameters (1–100).

### Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Dashboard

The Dashboard provides a structured view of the system status, predictions, signals, and performance metrics.

### Dashboard Pages

### Static Pages

| Page | Description |
|------|-------------|
| Overview | System overview with key metrics (predictions, signals, win rate, ROI) |
| Providers | Data provider health, success rates, and response times |
| Predictions | Prediction summaries and market breakdowns |
| Signals | Active signals and signal history |
| Backtesting | Backtest results and performance analysis |
| Statistics | Overall performance statistics |
| Health | System health status (providers, engines, cache, database) |
| Configuration | Application configuration view |

### Live Engine Pages

| Page | Endpoint | Description |
|------|----------|-------------|
| Live Overview | `GET /dashboard/live` | Live engine status overview |
| Live Matches | `GET /dashboard/live/matches` | Currently tracked matches with state and score |
| Workers | `GET /dashboard/live/workers` | Worker pool status and utilization |
| Heartbeat | `GET /dashboard/live/heartbeat` | System health heartbeat and component status |
| Live Metrics | `GET /dashboard/live/metrics` | Real-time performance metrics |
| Recent Events | `GET /dashboard/live/events` | Recent events published by the Live Engine |
| Provider Health | `GET /dashboard/live/providers` | Data provider health status |
| Queue Status | `GET /dashboard/live/queue` | Match processing queue status |

### Dashboard Widgets

Widgets are reusable Pydantic `Widget` components displayed on pages:

| Widget | Description |
|--------|-------------|
| `stat_widget` | Numeric stat with title, value, icon, and color |
| `health_widget` | Health status with color-coded indicator (green/yellow/red/gray) |
| `provider_widget` | Provider status with success rate and response time |
| `overview_widgets` | Pre-built set of 4 overview widgets |

### Dashboard Charts

Charts use `ChartProvider` to generate structured data compatible with Chart.js, D3, Plotly, etc.:

| Chart | Description |
|-------|-------------|
| `roi_chart` | ROI over time |
| `yield_chart` | Yield over time |
| `accuracy_chart` | Accuracy over time |
| `win_rate_chart` | Win rate over time |
| `confidence_distribution` | Prediction confidence histogram |
| `risk_distribution` | Signal risk histogram |
| `market_comparison` | Win rate + ROI by market type |
| `calibration_chart` | Expected vs observed probabilities |

## Application Layer

The Application Layer separates presentation from business logic:

```
REST Endpoint → Application Service → Engine → DTO Mapper → Response
```

This allows the same logic to be reused for REST API, Dashboard, CLI, Telegram, and Workers.

### Services

| Service | Purpose |
|---------|---------|
| `HealthService` | System health status from providers and engines |
| `MatchService` | Match data from the provider layer |
| `PredictionService` | Predictions from the Prediction Engine |
| `SignalService` | Signals from the Signal Engine |
| `BacktestingService` | Backtest execution and results |
| `StatisticsService` | Statistics aggregation from backtest results |
| `ProviderService` | Provider health and metadata |
| `ConfigurationService` | Application configuration |
| `LiveService` | Live engine status, matches, workers, events, metrics, heartbeat |

### DTOs (Data Transfer Objects)

All API responses use Pydantic DTOs — never internal engine models:

| DTO | Purpose |
|-----|---------|
| `HealthDTO` | System health (providers, engines, cache) |
| `MatchDTO` / `MatchListDTO` | Match data with pagination |
| `PredictionDTO` / `PredictionSummaryDTO` | Prediction results |
| `SignalDTO` / `SignalListDTO` | Signal data with pagination |
| `BacktestDTO` / `BacktestSummaryDTO` | Backtest results |
| `OverallStatisticsDTO` | Aggregate statistics |
| `MarketStatisticsDTO` | Per-market statistics |
| `LeagueStatisticsDTO` | Per-league statistics |
| `TeamStatisticsDTO` | Per-team statistics |
| `ProviderDTO` / `ProviderListDTO` | Provider health data |
| `ConfigurationDTO` | Application config |
| `LiveMatchDTO` | Live match data |
| `LiveEventDTO` | Live event data |
| `WorkerDTO` | Worker status data |
| `HeartbeatDTO` | Heartbeat status data |
| `LiveMetricsDTO` | Live engine metrics |
| `LiveStatusDTO` | Overall live engine status |
| `LiveSignalDTO` | Live signal data |

### Mapper

`app/application/mapper.py` converts internal engine models to DTOs:

```python
from app.application.mapper import Mapper

# Convert provider health to DTO
dto = Mapper.to_provider_dto("mock", provider.health_info)

# Convert backtest result to DTO
dto = Mapper.to_backtest_dto(backtest_result)

# Convert prediction to DTO
dto = Mapper.to_prediction_dto(prediction_result, home_team="Arsenal", away_team="Chelsea")
```

**Important**: Never return internal models directly from API endpoints. Always map through the Mapper layer.

## Composition Root & DI Container

All services are assembled in a centralized DI container (`app/core/container.py`).

### Container Architecture

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
```

### How It Works

1. **Container** creates and manages all singleton service instances
2. **Lazy initialization** — services are created on first access
3. **Type-safe** — all properties return concrete types
4. **Shared instances** — every engine shares the same providers, cache, AI, etc.

```python
from app.core.container import get_container

container = get_container()
ai = container.ai_engine
prediction = container.prediction_engine
signal = container.signal_engine
backtest = container.backtest_engine
```

### Dependency Injection Flow

```
app/core/container.py      → Composition Root — single source of truth
app/core/dependencies.py   → Public API — factory functions delegating to container
app/api/dependencies.py    → FastAPI Depends() functions for API endpoints
```

**Important**: Never create engine instances directly. Always use the DI system.

## Dashboard Architecture

The Dashboard follows a clean separation of concerns:

```
Application Service → DTO → Presenter → View
```

### Modules

| Module | Responsibility |
|--------|---------------|
| `views.py` | View layer (re-exports presenter for backward compatibility) |
| `presenters.py` | Transforms DTOs into dashboard-friendly ViewModels |
| `statistics.py` | Aggregated statistics for the dashboard view layer |
| `widgets.py` | Reusable widget components (Pydantic BaseModel) |
| `charts.py` | Chart data structures and providers (Pydantic BaseModel) |
| `pages.py` | Page layout compositions (Pydantic BaseModel) |
| `router.py` | API router for the dashboard root endpoint |

### How to Add a New Widget

1. Add a factory method to `WidgetFactory` in `app/dashboard/widgets.py`:

```python
@staticmethod
def my_widget(title: str, value: str) -> Widget:
    return Widget(title=title, value=value, icon="star", color="blue")
```

2. Use it in a page or presenter.

### How to Add a New Endpoint

1. Create a router in `app/api/routers/`:

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(service: MyService = Depends(get_my_service)):
    return await service.get_data()
```

2. Register in `app/main.py`:

```python
from app.api.routers import my_router
application.include_router(my_router, tags=["My Module"])
```

3. Add a dependency function in `app/api/dependencies.py`.
4. Add tests in `tests/test_api.py`.

### How to Add a New Dashboard Page

1. Add a factory method to `PageFactory` in `app/dashboard/pages.py`:

```python
@staticmethod
def my_page(widgets: list[Widget]) -> DashboardPage:
    return DashboardPage(
        title="My Page",
        description="Description of my page",
        widgets=widgets,
    )
```

2. Use it in the dashboard view layer.

## Dashboard Models

All Dashboard models (Widget, ChartData, ChartDataset, DashboardPage) use **Pydantic BaseModel** for:

- Automatic JSON serialization
- Field validation
- Consistency with the project-wide convention
- Compatibility with FastAPI response models

This was a deliberate architecture decision over `dataclass` to ensure the Dashboard layer aligns with the rest of the codebase where all serializable models use Pydantic.

## Dependency Injection

The project uses a three-tier DI system:

1. **Composition Root** (`app/core/container.py`) — creates and wires all services
2. **Public API** (`app/core/dependencies.py`) — factory functions that delegate to the container
3. **API Dependencies** (`app/api/dependencies.py`) — FastAPI `Depends()` functions

```python
# Factory functions in core/dependencies.py
from app.core.dependencies import (
    get_ai_engine,
    get_prediction_engine,
    get_signal_engine,
    get_backtesting_engine,
    get_provider_manager,
)

# FastAPI dependencies in api/dependencies.py
from app.api.dependencies import (
    get_health_service,
    get_match_service,
    get_prediction_service,
    get_signal_service,
    get_statistics_service,
)
```

## Health API

The `/health` endpoint returns:

- **System status**: healthy / degraded / unhealthy
- **Provider health**: name, status, success rate, response time, failures
- **Engine status**: AI, Prediction, Signal, Backtest engines
- **Cache status**: backend type and entry count
- **Database status**: connection state

## Statistics API

### Overall Statistics

`GET /statistics` returns `OverallStatisticsDTO`:

| Field | Description |
|-------|-------------|
| `total_predictions` | Total number of predictions made |
| `win_rate` | Win rate (0.0–1.0) |
| `roi` | Return on investment |
| `yield_pct` | Yield as percentage |
| `average_odds` | Average odds across predictions |
| `average_confidence` | Average prediction confidence |
| `brier_score` | Probability calibration quality |
| `calibration_error` | Expected Calibration Error |
| `signal_accuracy` | Signal accuracy rate |

### Aggregated Endpoints

`/statistics/roi`, `/statistics/yield`, and `/statistics/winrate` return the same `OverallStatisticsDTO`. They are convenience aliases for frontend clients that expect dedicated endpoints. The ROI, yield, and win rate values are all available in each response. This avoids duplicating business logic while providing the expected API surface.

### Breakdown Endpoints

- `/statistics/markets` — per-market statistics
- `/statistics/leagues` — per-league statistics
- `/statistics/teams` — per-team statistics (placeholder, not yet implemented)

## Provider Layer

See the full [Provider Layer documentation](#data-provider-platform) below.

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

# Formatting
ruff format .
```

---

## Live Engine

The Live Engine provides real-time match tracking, live predictions, and signal generation.

### Pipeline

```
Scheduler → Discovery → Queue → Worker → Provider → AI → Prediction → Signal → Publisher
```

### Components

| Component | File | Description |
|-----------|------|-------------|
| `LiveEngine` | `app/live/engine.py` | Main entry point, coordinates all components |
| `LiveScheduler` | `app/live/scheduler.py` | Periodic discovery cycle scheduler (APScheduler) |
| `LiveCoordinator` | `app/live/coordinator.py` | Orchestrates discovery → queue → worker dispatch |
| `LiveWorker` | `app/live/worker.py` | Processes individual matches through the full pipeline |
| `MatchQueue` | `app/live/queue.py` | Priority queue for match processing order |
| `MatchDiscovery` | `app/live/matcher.py` | Discovers upcoming and live matches via Provider Layer |
| `EventPublisher` | `app/live/publisher.py` | Broadcasts events to all subscribers (REST, Dashboard, Telegram) |
| `EventDispatcher` | `app/live/dispatcher.py` | Routes events through the Publisher |
| `StateRegistry` | `app/live/state.py` | Central state for matches, workers, and engine health |
| `HeartbeatMonitor` | `app/live/heartbeat.py` | Periodic health monitoring (workers, providers, scheduler) |
| `LiveMetricsCollector` | `app/live/metrics.py` | Collects and reports performance metrics |
| `LiveComponentRegistry` | `app/live/registry.py` | Registry for accessing all Live Engine sub-components |

### Live Engine Architecture

```
app/live/
├── engine.py            # Main LiveEngine entry point
├── scheduler.py         # Periodic discovery cycle (APScheduler)
├── coordinator.py       # Orchestrates discovery → queue → worker
├── worker.py            # Processes individual matches
├── queue.py             # Priority match processing queue
├── matcher.py           # Match discovery via Provider Layer
├── events.py            # Event models and factory
├── publisher.py         # Event broadcasting to subscribers
├── dispatcher.py        # Event routing to channels
├── state.py             # State registry for matches and workers
├── models.py            # Pydantic models (LiveMatch, WorkerInfo, etc.)
├── interfaces.py        # Abstract interfaces for all components
├── exceptions.py        # Custom exceptions
├── heartbeat.py         # Health monitoring
├── metrics.py           # Performance metrics collection
├── logging_context.py   # Structured logging (correlation ID, worker ID, etc.)
├── recovery.py          # Recovery layer (worker, provider, queue, scheduler)
└── registry.py          # Component registry
```

### Live Engine Pipeline

1. **Scheduler** triggers a discovery cycle at configurable intervals
2. **Discovery** fetches upcoming and live matches from the Provider Layer
3. **Queue** enqueues matches (priority queue for LIVE/HALF_TIME states)
4. **Workers** process matches in parallel (configurable pool size)
5. **Pipeline** per match: Provider Update → AI Analysis → Prediction → Signal
6. **Publisher** broadcasts events to all registered handlers
7. **State Registry** tracks match states, worker health, and engine metrics

### How It Works

```python
from app.core.container import get_container

container = get_container()
live_engine = container.live_engine
await live_engine.start()  # Starts scheduler, heartbeat, workers
# ... application runs ...
await live_engine.stop()   # Graceful shutdown
```

### Event Types

| Event | Description |
|-------|-------------|
| `match_started` | Match transitions to LIVE |
| `prediction_updated` | Predictions are updated for a live match |
| `signal_created` | New signal generated for a live match |
| `signal_updated` | Existing signal updated |
| `goal` | Goal scored |
| `odds_changed` | Odds change significantly |
| `match_finished` | Match finishes |
| `heartbeat` | Periodic health event |

### How to Add a New Event

1. Add event class in `app/live/events.py`:

```python
class MyNewEvent(LiveEvent):
    event_type: str = "my_new_event"
```

2. Add factory method in `EventFactory`:

```python
@staticmethod
def my_new_event(fixture_id: int, **kwargs) -> MyNewEvent:
    return MyNewEvent(event_id=f"evt_{uuid.uuid4().hex[:12]}", fixture_id=fixture_id, data=kwargs)
```

3. Use the factory in the Worker pipeline or other components.

### How to Add a New Worker

Workers implement the `WorkerInterface` and are created by the `LiveEngine`:

```python
class LiveWorker(WorkerInterface):
    async def process(self, match: LiveMatch) -> list[LiveEvent]:
        # Implement pipeline: Provider → AI → Prediction → Signal
        ...
```

Workers are configured via the `LiveEngine` constructor (`num_workers` parameter) and receive engines via Dependency Injection (not Service Locator).

### How to Add a New Publisher

Publishers are handlers registered with the `EventPublisher`:

```python
async def my_handler(event: LiveEvent) -> None:
    # Process the event (e.g., send to WebSocket, log, etc.)
    ...

publisher.register(my_handler)
```

### How Recovery Works

The Recovery Layer provides fault tolerance for all critical components:

| Recovery | Triggers On | Action |
|----------|-------------|--------|
| `WorkerRecovery` | Worker pipeline failure | Restart worker with exponential backoff |
| `SchedulerRecovery` | Scheduler cycle failure | Restart coordinator cycle |
| `ProviderFailureRecovery` | Provider failure | Reconnect with retry policy |
| `QueueRecovery` | Queue stuck/corrupted | Clear stale entries |

All recovery mechanisms use a configurable `RetryPolicy` with exponential backoff.

### Structured Logging

All Live Engine logs include structured context fields via `LogContext`:

| Field | Description |
|-------|-------------|
| `correlation_id` | Traces a request across components |
| `worker_id` | Identifies which worker is processing |
| `match_id` | Identifies which match is being processed |
| `event_id` | Identifies which event is being processed |
| `scheduler_cycle` | Identifies which scheduler cycle is running |
| `execution_time_ms` | Tracks how long an operation took |
| `provider_time_ms` | Tracks provider response time |

```python
from app.live.logging_context import LogContext, Timer, log_with_context

ctx = LogContext(correlation_id="abc123", worker_id="worker_0", match_id=12345)
with ctx:
    with Timer() as timer:
        result = await do_work()
    log_with_context(logger, "info", f"Done in {timer.elapsed_ms:.1f}ms")
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

---

## Data Provider Platform

The Provider Layer is a production-ready data abstraction layer that provides a unified interface for fetching football data from multiple sources.

### Provider Architecture

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

### Provider Lifecycle

Providers are managed through the `ProviderManager` which handles the full lifecycle:

1. **Registration**: Providers are registered via `ProviderRegistry.register()`
2. **Startup**: `ProviderManager.start()` opens HTTP clients for all providers
3. **Runtime**: Requests flow through fallback/failover chains with health-based routing
4. **Shutdown**: `ProviderManager.stop()` gracefully closes all HTTP clients

The lifecycle is integrated into the FastAPI application lifespan in `main.py`.

### Registry

The `ProviderRegistry` manages provider instances via a public API:

```python
from app.providers.registry import ProviderRegistry

registry = ProviderRegistry()
registry.register(MockProvider(priority=100))

# Public API methods
provider = registry.get("mock")           # Get by name
all_providers = registry.get_all()        # Sorted by priority
enabled = registry.get_enabled()          # Only enabled providers
names = registry.names()                  # List of names
items = registry.items()                  # (name, provider) pairs
values = registry.values()                # All provider instances
```

### How to Add a New Provider

1. Create a new adapter in `app/providers/adapters/`:

```python
from app.providers.base import BaseProvider
from app.providers.models import Competition, Fixture, ProviderStatus

class MyProvider(BaseProvider):
    def __init__(self, api_key: str, priority: int = 50) -> None:
        super().__init__(name="my_provider", api_key=api_key, priority=priority)

    async def check_health(self) -> ProviderStatus:
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

---

## Backtesting Platform

The Backtesting Platform validates system quality against historical matches.

### Pipeline

```
Historical Matches → Provider Layer → AI Analysis → Prediction → Signal → Backtesting → Metrics → Reports
```

### Scopes

| Scope | Description |
|-------|-------------|
| `SINGLE_MATCH` | Single fixture by ID |
| `LEAGUE` | All matches in a league |
| `SEASON` | All matches in a season |
| `DATE_RANGE` | Matches within a date range |
| `ALL` | All available matches |

### Key Metrics

| Metric | Description |
|--------|-------------|
| Win Rate | Percentage of correct predictions |
| ROI | Return on investment |
| Yield | ROI as percentage |
| Brier Score | Probability calibration quality |
| Calibration Error | Expected Calibration Error (ECE) |

### Running a Backtest

```python
from app.core.dependencies import get_backtesting_engine
from app.backtesting.models import BacktestRequest, BacktestScope

engine = get_backtesting_engine()
result = await engine.run(
    BacktestRequest(scope=BacktestScope.SINGLE_MATCH, fixture_id=12345)
)
```

## Signal Engine

The Signal Engine evaluates Prediction Results, assessing quality, risk, and value.

### Pipeline

```
PredictionResult → Validation → Generation → Filtering → Deduplication → Cooldown → Scoring → Ranking → Signal
```

### Signal Generators

| Generator | Market | Description |
|-----------|--------|-------------|
| `WinnerSignalGenerator` | MATCH_WINNER | Home/Draw/Away |
| `OverUnderSignalGenerator` | OVER_UNDER_25 | Over/Under goals |
| `BTTSSignalGenerator` | BTTS | Both Teams To Score |
| `HandicapSignalGenerator` | ASIAN_HANDICAP | Asian handicap |
| `ValueSignalGenerator` | All markets | Value bet detection |
| `LiveSignalGenerator` | All markets | Live match signals |

### Value Categories

| Category | EV Range | Description |
|----------|----------|-------------|
| STRONG_VALUE | ≥ 0.08 | High confidence value bet |
| VALUE | ≥ 0.03 | Moderate value |
| NEUTRAL | 0 to 0.03 | No clear edge |
| NEGATIVE_EV | < 0 | Not recommended |
