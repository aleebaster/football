"""Tests for REST API — integration tests for all endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealthAPI:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "providers" in data
        assert "engines" in data

    @pytest.mark.asyncio
    async def test_health_has_engines(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        data = response.json()
        assert len(data["engines"]) == 5
        engine_names = [e["name"] for e in data["engines"]]
        assert "AI Engine" in engine_names
        assert "Prediction Engine" in engine_names
        assert "Signal Engine" in engine_names
        assert "Backtest Engine" in engine_names
        assert "Live Engine" in engine_names


class TestRootAPI:
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient) -> None:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Football Analysis" in data["message"]


class TestMatchesAPI:
    @pytest.mark.asyncio
    async def test_get_matches(self, client: AsyncClient) -> None:
        response = await client.get("/matches")
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_get_matches_with_limit(self, client: AsyncClient) -> None:
        response = await client.get("/matches?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["matches"], list)


class TestPredictionsAPI:
    @pytest.mark.asyncio
    async def test_get_prediction(self, client: AsyncClient) -> None:
        response = await client.get("/predictions/1000")
        assert response.status_code == 200
        data = response.json()
        assert data["fixture_id"] == 1000
        assert "overall_confidence" in data

    @pytest.mark.asyncio
    async def test_get_prediction_summary(self, client: AsyncClient) -> None:
        response = await client.get("/predictions/1000/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["fixture_id"] == 1000
        assert "home_win_pct" in data


class TestSignalsAPI:
    @pytest.mark.asyncio
    async def test_get_signals(self, client: AsyncClient) -> None:
        response = await client.get("/signals")
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_signals_with_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/signals?page=1&page_size=10")
        assert response.status_code == 200


class TestBacktestingAPI:
    @pytest.mark.asyncio
    async def test_get_backtests(self, client: AsyncClient) -> None:
        response = await client.get("/backtests")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestStatisticsAPI:
    @pytest.mark.asyncio
    async def test_get_statistics(self, client: AsyncClient) -> None:
        response = await client.get("/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
        assert "win_rate" in data
        assert "roi" in data

    @pytest.mark.asyncio
    async def test_get_statistics_roi(self, client: AsyncClient) -> None:
        response = await client.get("/statistics/roi")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_statistics_yield(self, client: AsyncClient) -> None:
        response = await client.get("/statistics/yield")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_statistics_winrate(self, client: AsyncClient) -> None:
        response = await client.get("/statistics/winrate")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_statistics_markets(self, client: AsyncClient) -> None:
        response = await client.get("/statistics/markets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_statistics_leagues(self, client: AsyncClient) -> None:
        response = await client.get("/statistics/leagues")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_statistics_teams(self, client: AsyncClient) -> None:
        response = await client.get("/statistics/teams")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestProvidersAPI:
    @pytest.mark.asyncio
    async def test_get_providers(self, client: AsyncClient) -> None:
        response = await client.get("/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "total" in data
        assert "healthy" in data


class TestConfigurationAPI:
    @pytest.mark.asyncio
    async def test_get_configuration(self, client: AsyncClient) -> None:
        response = await client.get("/configuration")
        assert response.status_code == 200
        data = response.json()
        assert "project_name" in data
        assert "version" in data
        assert "debug" in data
