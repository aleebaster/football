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
