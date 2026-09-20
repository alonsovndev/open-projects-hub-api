import pytest

from src.app.config.app_config import AppConfig
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


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
        role=UserRole.ADMIN.value,
    )


@pytest.fixture
def viewer_token(app_jwt_handler):
    """Generate valid viewer JWT token."""
    return app_jwt_handler.create_access_token(
        user_id="viewer-456",
        email="viewer@example.com",
        role=UserRole.VIEWER.value,
    )


class TestAuthDependencies:
    def test_get_current_user_without_token_returns_401(self, client):
        """Test accessing auth-required route without Authorization header returns 401."""
        response = client.get("/v1/users/00000000-0000-0000-0000-000000000001")

        assert response.status_code == 401

    def test_get_current_user_with_invalid_token_returns_401(self, client):
        """Test accessing auth-required route with malformed token returns 401."""
        response = client.get(
            "/v1/users/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    def test_create_user_without_token_returns_401(self, client):
        """Test accessing admin-only user creation route without Authorization header returns 401."""
        response = client.post(
            "/v1/users",
            json={
                "email": "new@example.com",
                "password": "Password123",
                "firstName": "New",
                "lastName": "User",
            },
        )

        assert response.status_code == 401

    def test_create_user_with_viewer_token_returns_403(self, client, viewer_token):
        """Test accessing admin-only user creation route with a viewer token returns 403."""
        response = client.post(
            "/v1/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={
                "email": "new@example.com",
                "password": "Password123",
                "firstName": "New",
                "lastName": "User",
            },
        )

        assert response.status_code == 403
