"""
Tests for health check endpoints (combined, liveness, and readiness).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.app import fastApiApp


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(fastApiApp)


class TestHealthCheck:
    """Test combined health check endpoint (legacy)."""

    @patch("src.app.shared.presentation.health_checks.get_engine")
    def test_health_check_returns_healthy_when_database_connected(self, mock_get_engine, client):
        """Verify health check returns 200 when database is connected."""
        # Mock successful database connection with proper async context manager
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(return_value=None)

        # Create a proper async context manager mock
        mock_connection_ctx = AsyncMock()
        mock_connection_ctx.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_connection_ctx)

        mock_db = MagicMock()
        mock_db.engine = mock_engine
        mock_get_engine.return_value = mock_db

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "service" in data
        assert "version" in data

    @patch("src.app.shared.presentation.health_checks.get_engine")
    def test_health_check_returns_unhealthy_when_database_disconnected(self, mock_get_engine, client):
        """Verify health check returns 503 when database is unreachable."""
        # Mock database connection failure with async context manager
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(side_effect=Exception("Database connection failed"))

        # Create a proper async context manager mock
        mock_connection_ctx = AsyncMock()
        mock_connection_ctx.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_connection_ctx)

        mock_db = MagicMock()
        mock_db.engine = mock_engine
        mock_get_engine.return_value = mock_db

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert data["error"] == "database_unreachable"
        assert "service" in data
        assert "version" in data


class TestLivenessProbe:
    """Test Kubernetes liveness probe endpoint."""

    def test_liveness_returns_200_always(self, client):
        """Verify liveness probe always returns 200 (process is alive)."""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "alive"
        assert "service" in data
        assert "version" in data

    def test_liveness_does_not_check_database(self, client):
        """Verify liveness probe doesn't check database (lightweight check)."""
        # Should succeed even without mocking database
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()

        # Should not have database field
        assert "database" not in data
        assert "checks" not in data


class TestReadinessProbe:
    """Test Kubernetes readiness probe endpoint."""

    @patch("src.app.shared.presentation.health_checks.get_engine")
    def test_readiness_returns_200_when_database_connected(self, mock_get_engine, client):
        """Verify readiness probe returns 200 when database is connected."""
        # Mock successful database connection with proper async context manager
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(return_value=None)

        # Create a proper async context manager mock
        mock_connection_ctx = AsyncMock()
        mock_connection_ctx.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_connection_ctx)

        mock_db = MagicMock()
        mock_db.engine = mock_engine
        mock_get_engine.return_value = mock_db

        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ready"
        assert data["checks"]["database"] == "connected"
        assert "service" in data
        assert "version" in data

    @patch("src.app.shared.presentation.health_checks.get_engine")
    def test_readiness_returns_503_when_database_disconnected(self, mock_get_engine, client):
        """Verify readiness probe returns 503 when database is unreachable."""
        # Mock database connection failure with proper async context manager
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(side_effect=Exception("Database connection failed"))

        # Create a proper async context manager mock
        mock_connection_ctx = AsyncMock()
        mock_connection_ctx.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_connection_ctx)

        mock_db = MagicMock()
        mock_db.engine = mock_engine
        mock_get_engine.return_value = mock_db

        response = client.get("/health/ready")

        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "not_ready"
        assert data["checks"]["database"] == "disconnected"
        assert data["error"] == "database_unreachable"
        assert "service" in data
        assert "version" in data

    @patch("src.app.shared.presentation.health_checks.get_engine")
    def test_readiness_checks_structure(self, mock_get_engine, client):
        """Verify readiness probe returns proper checks structure."""
        # Mock successful database connection with proper async context manager
        mock_connection = AsyncMock()
        mock_connection.execute = AsyncMock(return_value=None)

        # Create a proper async context manager mock
        mock_connection_ctx = AsyncMock()
        mock_connection_ctx.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_connection_ctx)

        mock_db = MagicMock()
        mock_db.engine = mock_engine
        mock_get_engine.return_value = mock_db

        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()

        # Verify structure includes checks object
        assert "checks" in data
        assert isinstance(data["checks"], dict)
        assert "database" in data["checks"]
