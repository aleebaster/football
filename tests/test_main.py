"""Tests for main application module."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestMainApp:
    """Tests for the main FastAPI application."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self) -> None:
        """Test root endpoint returns welcome message."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Football Analysis" in data["message"]

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test health check endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
