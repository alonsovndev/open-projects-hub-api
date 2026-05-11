"""
Tests for health check endpoint.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.app.app import fastApiApp


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(fastApiApp)


class TestHealthCheck:
    """Test health check endpoint."""

    @patch("src.app.shared.presentation.dependencies.get_db_connection")
    def test_health_check_returns_healthy_when_database_connected(self, mock_get_db, client):
        """Verify health check returns 200 when database is connected."""
        # Mock successful database connection
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(return_value=None)
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock(return_value=None)
        
        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        
        mock_db = MagicMock()
        mock_db.engine = mock_engine
        mock_get_db.return_value = mock_db
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "service" in data
        assert "version" in data

    @patch("src.app.shared.presentation.dependencies.get_db_connection")
    def test_health_check_returns_unhealthy_when_database_disconnected(self, mock_get_db, client):
        """Verify health check returns 503 when database is unreachable."""
        # Mock database connection failure with async context manager
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(side_effect=Exception("Database connection failed"))
        
        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_connection)
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock(return_value=None)
        
        mock_db = MagicMock()
        mock_db.engine = mock_engine
        mock_get_db.return_value = mock_db
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert data["error"] == "database_unreachable"
        assert "service" in data
        assert "version" in data
