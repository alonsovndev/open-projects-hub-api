import pytest
from fastapi.testclient import TestClient

from src.app.app import fastApiApp
from src.app.config.app_config import AppConfig
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


@pytest.fixture
def client():
    return TestClient(fastApiApp)


@pytest.fixture
def app_jwt_handler():
    """JWT handler using the app's configured secret key."""
    config = AppConfig.instance()
    secret_key = config.get_config("jwt.secret_key")
    return JWTHandler(secret_key=secret_key, expiration_minutes=60, validate_secret=False)


@pytest.fixture
def admin_token(app_jwt_handler):
    """Generate valid admin JWT token."""
    return app_jwt_handler.create_access_token(
        user_id="admin-123",
        email="admin@example.com",
        role="ADMIN",
    )


@pytest.fixture
def user_token(app_jwt_handler):
    """Generate valid user JWT token."""
    return app_jwt_handler.create_access_token(
        user_id="user-456",
        email="user@example.com",
        role="USER",
    )


class TestAuthDependencies:

    def test_get_current_user_without_token_returns_403(self, client):
        """Test accessing auth-required route without Authorization header returns 403.

        FastAPI's HTTPBearer returns 403 (not 401) when no credentials are provided.
        """
        response = client.get("/v1/users/00000000-0000-0000-0000-000000000001")

        assert response.status_code == 403

    def test_get_current_user_with_invalid_token_returns_401(self, client):
        """Test accessing auth-required route with malformed token returns 401."""
        response = client.get(
            "/v1/users/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    def test_register_without_token_returns_403(self, client):
        """Test accessing admin-only user creation route without Authorization header returns 403."""
        response = client.post(
            "/v1/users",
            json={
                "email": "new@example.com",
                "password": "Password123",
                "firstName": "New",
                "lastName": "User",
            },
        )

        assert response.status_code == 403

    def test_register_with_user_token_returns_403(self, client, user_token):
        """Test accessing admin-only user creation route with non-admin token returns 403."""
        response = client.post(
            "/v1/users",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "email": "new@example.com",
                "password": "Password123",
                "firstName": "New",
                "lastName": "User",
            },
        )

        assert response.status_code == 403
