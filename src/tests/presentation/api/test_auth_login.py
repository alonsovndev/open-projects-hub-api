import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.app.app import fastApiApp
from src.app.features.domain.entities.user_entity import UserEntity
from src.app.features.domain.value_objects.email import Email
from src.app.features.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


@pytest.fixture
def client():
    return TestClient(fastApiApp)


@pytest.fixture
def mock_admin_user():
    """Fixture for an admin user entity."""
    password_hash = PasswordHandler.hash_password("Admin123!")

    return UserEntity(
        id=EntityId.generate(),
        email=Email("admin@example.com"),
        first_name="Admin",
        last_name="User",
        password_hash=password_hash,
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_regular_user():
    """Fixture for a regular user entity."""
    password_hash = PasswordHandler.hash_password("User123!")

    return UserEntity(
        id=EntityId.generate(),
        email=Email("user@example.com"),
        first_name="Regular",
        last_name="User",
        password_hash=password_hash,
        role=UserRole.USER,
    )


class TestLoginEndpoint:

    def test_login_success_returns_frontend_shape(self, client, mock_admin_user):
        """Test successful admin login returns correct response shape."""
        with patch(
            "src.app.features.infrastructure.repository.user_repository_impl.UserRepositoryImpl.find_by_email",
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
        assert data["role"] == "ADMIN"

        assert "user" in data
        assert data["user"]["email"] == "admin@example.com"
        assert data["user"]["displayName"] == "Admin User"
        assert data["user"]["name"] == "Admin User"
        assert data["user"]["role"] == "ADMIN"

    def test_login_success_with_regular_user(self, client, mock_regular_user):
        """Test successful regular user login."""
        with patch(
            "src.app.features.infrastructure.repository.user_repository_impl.UserRepositoryImpl.find_by_email",
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
        assert data["role"] == "USER"
        assert data["displayName"] == "Regular User"

    def test_login_with_nonexistent_email_returns_401(self, client):
        """Test login with non-existent email returns 401."""
        with patch(
            "src.app.features.infrastructure.repository.user_repository_impl.UserRepositoryImpl.find_by_email",
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
            "src.app.features.infrastructure.repository.user_repository_impl.UserRepositoryImpl.find_by_email",
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
            "src.app.features.infrastructure.repository.user_repository_impl.UserRepositoryImpl.find_by_email",
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
        payload = pyjwt.decode(token, secret_key, algorithms=["HS256"])

        assert payload["email"] == "admin@example.com"
        assert payload["role"] == "ADMIN"
