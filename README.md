# Football Analysis Platform

A scalable football match analysis and prediction platform with Telegram bot integration.

## 🏗️ Architecture

This project follows a modular, scalable architecture designed for production use:

```
football/
├── app/                          # Main application package
│   ├── config/                   # Configuration management
│   ├── core/                     # Core utilities and DI
│   ├── database/                 # Database layer (SQLAlchemy + Alembic)
│   │   ├── models/               # ORM models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Database services
│   │   ├── providers/            # External data providers
│   │   └── migrations/           # Alembic migrations
│   ├── telegram/                 # Telegram bot module
│   │   ├── handlers/             # Command/message handlers
│   │   ├── keyboards/            # Inline/reply keyboards
│   │   ├── middlewares/           # Bot middlewares
│   │   └── routers/              # Handler routers
│   ├── analysis/                 # Betting analysis
│   ├── simulation/               # Monte Carlo simulations
│   ├── signals/                  # Betting signals
│   ├── monitoring/               # Health & metrics
│   ├── scheduler/                # APScheduler tasks
│   ├── dashboard/                # FastAPI web interface
│   ├── cache/                    # Caching (memory/Redis)
│   ├── utils/                    # Utility functions
│   └── logging/                  # Loguru configuration
├── tests/                        # Test suite
├── scripts/                      # CLI scripts
├── docker/                       # Docker configuration
├── docs/                         # Documentation
└── .github/workflows/            # CI/CD pipelines
```

## 🚀 Features

- **Async-First**: Fully asynchronous Python 3.12+ architecture
- **Type-Safe**: Complete type hints with mypy support
- **Modular Design**: Independent modules with dependency injection
- **Database Agnostic**: SQLite now, PostgreSQL-ready without code changes
- **Cache Flexible**: In-memory cache with Redis-ready architecture
- **Production Ready**: Docker, CI/CD, logging, monitoring
- **Telegram Bot**: Full-featured bot with handlers and keyboards
- **FastAPI Dashboard**: REST API with automatic documentation

## 📋 Prerequisites

- Python 3.12+
- pip or poetry
- Docker (optional)

## 🛠️ Installation

### Local Development

1. **Clone the repository:**

```bash
git clone https://github.com/aleebaster/football.git
cd football
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database:**

```bash
python scripts/db.py init
```

6. **Run the application:**

```bash
python -m app.main
```

### Docker

1. **Build and run with Docker Compose:**

```bash
cd docker
docker-compose up -d
```

2. **Or build manually:**

```bash
docker build -f docker/Dockerfile -t football-analysis .
docker run -p 8000:8000 --env-file .env football-analysis
```

## ⚙️ Configuration

All configuration is managed through environment variables or `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram Bot API token | Required |
| `ADMIN_ID` | Telegram admin user ID | Required |
| `DATABASE_URL` | Database connection URL | `sqlite+aiosqlite:///football.db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LANGUAGE` | Application language | `uk` |
| `UPDATE_INTERVAL` | Data update interval (seconds) | `300` |
| `MIN_EXPECTED_VALUE` | Minimum EV threshold | `5` |
| `MIN_PROFIT` | Minimum profit threshold | `3` |
| `CACHE_TTL` | Cache TTL (seconds) | `300` |
| `DASHBOARD_PORT` | FastAPI port | `8000` |

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_config.py -v
```

### Code Quality

```bash
# Lint with ruff
ruff check app/ tests/
ruff format app/ tests/

# Type check
mypy app/
```

## 📦 Development

### Adding New Modules

1. Create module directory under `app/`
2. Add `__init__.py`
3. Implement functionality
4. Register in `app/main.py` if needed
5. Add tests

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🐳 Docker Services

The `docker-compose.yml` includes:

- **app**: Main application
- **postgres**: PostgreSQL database (optional)
- **redis**: Redis cache (optional)

## 📊 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Welcome message |
| `GET /health` | Health check |
| `GET /status` | Application status |
| `GET /docs` | Swagger documentation |

## 🔧 Development Tools

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### Database Management

```bash
# Initialize database
python scripts/db.py init

# Reset database
python scripts/db.py reset
```

## 📝 Code Style

- **Formatter**: Black + Ruff
- **Linter**: Ruff
- **Type Checker**: mypy (strict mode)
- **Line Length**: 88 characters

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Python 3.12+
- FastAPI
- SQLAlchemy 2
- Pydantic v2
- python-telegram-bot
- Loguru
- Alembic
