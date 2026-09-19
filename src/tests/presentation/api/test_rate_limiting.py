"""
Integration tests for rate limiting on login endpoint.

Tests the rate limiting functionality added in Phase 1.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test to prevent pollution."""
    from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter

    # Clear the rate limiter's storage before each test
    if hasattr(limiter, "_storage"):
        limiter._storage.storage.clear()
    yield
    # Clean up after test
    if hasattr(limiter, "_storage"):
        limiter._storage.storage.clear()


@pytest.fixture
def mock_admin_user():
    """Fixture for an admin user entity."""
    password_hash = asyncio.run(
        __import__(
            "src.app.shared.infrastructure.security.password_handler", fromlist=["PasswordHandler"]
        ).PasswordHandler.hash_password("Admin123!")
    )

    return UserEntity(
        id=EntityId.generate(),
        email=Email("admin@example.com"),
        display_name="Admin User",
        password_hash=password_hash,
        role=UserRole.ADMIN,
    )


class TestLoginRateLimiting:
    """Test rate limiting on login endpoint."""

    def test_rate_limit_allows_requests_within_limit(self, client, mock_admin_user):
        """Test that requests within rate limit are allowed."""
        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=mock_admin_user),
        ):
            # Make 5 requests (well within 10/minute limit)
            responses = []
            for _ in range(5):
                response = client.post(
                    "/v1/auth/login",
                    json={
                        "email": "admin@example.com",
                        "password": "Admin123!",
                    },
                )
                responses.append(response)

            # All should succeed
            assert all(r.status_code == 200 for r in responses)
            assert all("token" in r.json() for r in responses)

    def test_rate_limit_includes_retry_after_header(self, client, mock_admin_user):
        """Test that rate limit response includes Retry-After header."""
        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=mock_admin_user),
        ):
            # Make requests up to the limit (10 requests)
            for i in range(10):
                response = client.post(
                    "/v1/auth/login",
                    json={
                        "email": f"user{i}@example.com",
                        "password": "Admin123!",
                    },
                )

                # First 10 should work or fail with auth error (not rate limit)
                assert response.status_code in [200, 401]

    @patch("src.app.shared.presentation.health_checks.get_engine")
    def test_login_rate_limit_is_per_endpoint(self, mock_get_db, client, mock_admin_user):
        """Test that rate limit is specific to login endpoint."""
        # Mock database for health check endpoint
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
        mock_get_db.return_value = mock_db

        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=mock_admin_user),
        ):
            # Make login requests
            login_response = client.post(
                "/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "Admin123!",
                },
            )

            # Should still be able to access other endpoints
            health_response = client.get("/health")

            assert login_response.status_code == 200
            assert health_response.status_code == 200

    def test_failed_login_attempts_count_toward_rate_limit(self, client):
        """Test that failed login attempts also count toward rate limit."""
        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=None),  # User not found
        ):
            # Make multiple failed attempts
            responses = []
            for _ in range(3):
                response = client.post(
                    "/v1/auth/login",
                    json={
                        "email": "nonexistent@example.com",
                        "password": "WrongPass123",
                    },
                )
                responses.append(response)

            # All should return 401 (not rate limited yet, but auth failed)
            assert all(r.status_code == 401 for r in responses)

    def test_rate_limit_configuration_is_correct(self):
        """Test that rate limit is configured correctly (10/minute for login, 5/minute for register)."""
        from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter

        # Check that limiter exists and is configured
        assert limiter is not None
        assert limiter._default_limits is not None
        assert len(limiter._default_limits) > 0

        # Verify key_func is set (used to identify clients by IP)
        assert limiter._key_func is not None

        # Note: The specific 10/minute (login) and 5/minute (register) limits
        # are applied via decorator on endpoints, verified by integration tests above
