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
