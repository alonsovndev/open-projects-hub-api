import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


def _hash_password_sync(password: str) -> str:
    """Helper to hash password synchronously for test fixtures."""
    return asyncio.run(PasswordHandler.hash_password(password))


@pytest.fixture
def mock_admin_user():
    """Fixture for an admin user entity."""
    password_hash = _hash_password_sync("Admin123!")

    return UserEntity(
        id=EntityId.generate(),
        email=Email("admin@example.com"),
        display_name="Admin User",
        password_hash=password_hash,
        role=UserRole.ADMIN,
        email_verified_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_regular_user():
    """Fixture for a regular user entity."""
    password_hash = _hash_password_sync("User123!")

    return UserEntity(
        id=EntityId.generate(),
        email=Email("user@example.com"),
        display_name="Regular User",
        password_hash=password_hash,
        role=UserRole.VIEWER,
        email_verified_at=datetime.now(UTC),
    )


class TestLoginEndpoint:
    def test_login_success_returns_frontend_shape(self, client, mock_admin_user):
        """Test successful admin login returns correct response shape."""
        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=mock_admin_user),
        ):
            response = client.post(
                "/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "Admin123!",
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert "token" in data
        assert "accessToken" in data
        assert data["token"] == data["accessToken"]
        assert data["email"] == "admin@example.com"
        assert data["displayName"] == "Admin User"
        assert "loggedInAt" in data
        assert data["role"] == "admin"

        assert "user" in data
        assert data["user"]["email"] == "admin@example.com"
        assert data["user"]["displayName"] == "Admin User"
        assert data["user"]["name"] == "Admin User"
        assert data["user"]["role"] == "admin"

    def test_login_success_with_regular_user(self, client, mock_regular_user):
        """Test successful regular user login."""
        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=mock_regular_user),
        ):
            response = client.post(
                "/v1/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "User123!",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "viewer"
        assert data["displayName"] == "Regular User"

    def test_login_with_nonexistent_email_returns_401(self, client):
        """Test login with non-existent email returns 401."""
        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=None),
        ):
            response = client.post(
                "/v1/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "SomePassword",
                },
            )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_with_wrong_password_returns_401(self, client, mock_admin_user):
        """Test login with incorrect password returns 401."""
        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=mock_admin_user),
        ):
            response = client.post(
                "/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "WrongPassword",
                },
            )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_with_missing_password_returns_422(self, client):
        """Test login with missing password field returns 422."""
        response = client.post(
            "/v1/auth/login",
            json={"email": "admin@example.com"},
        )

        assert response.status_code == 422

    def test_login_with_missing_email_returns_422(self, client):
        """Test login with missing email field returns 422."""
        response = client.post(
            "/v1/auth/login",
            json={"password": "SomePassword"},
        )

        assert response.status_code == 422

    def test_login_with_invalid_email_format_returns_422(self, client):
        """Test login with invalid email format returns 422."""
        response = client.post(
            "/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "SomePassword",
            },
        )

        assert response.status_code == 422

    def test_login_token_is_valid_jwt(self, client, mock_admin_user):
        """Test that the returned token is a valid JWT."""
        import jwt as pyjwt

        from src.app.config.app_config import AppConfig

        with patch(
            "src.app.features.user.infrastructure.repositories.user_repository_impl.UserRepositoryImpl.find_by_email",
            new=AsyncMock(return_value=mock_admin_user),
        ):
            response = client.post(
                "/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "Admin123!",
                },
            )

        assert response.status_code == 200
        token = response.json()["token"]

        config = AppConfig.instance()
        secret_key = config.get_config("jwt.secret_key")
        payload = pyjwt.decode(
            token,
            secret_key,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_iss": False},
        )

        assert payload["email"] == "admin@example.com"
        assert payload["role"] == "admin"
