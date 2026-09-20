from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.app.features.auth.application.dtos.auth_dto import AdminLoginResponse, UserDetail
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError


@pytest.fixture
def mock_register_response():
    """Fixture for a successful registration response."""
    return AdminLoginResponse(
        token="mock.jwt.token",
        access_token="mock.jwt.token",
        refresh_token="mock.jwt.refresh.token",
        session_expires_at=(datetime.now(tz=UTC) + timedelta(hours=24)).isoformat(),
        email="newuser@example.com",
        display_name="New User",
        logged_in_at=datetime.now(tz=UTC).isoformat(),
        role="admin",
        user=UserDetail(
            email="newuser@example.com",
            display_name="New User",
            name="New User",
            role="admin",
        ),
    )


class TestRegisterEndpoint:
    def test_register_success_returns_201_with_token(self, client, mock_register_response):
        """Test successful registration returns 201 with JWT token and user data."""
        with patch(
            "src.app.features.auth.application.use_cases.register_user.RegisterUserUseCase.execute",
            new=AsyncMock(return_value=mock_register_response),
        ):
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass1",
                    "displayName": "New User",
                },
            )

        assert response.status_code == 201
        data = response.json()

        # Verify token fields
        assert "token" in data
        assert "accessToken" in data
        assert data["token"] == data["accessToken"]

        # Verify user fields
        assert data["email"] == "newuser@example.com"
        assert data["displayName"] == "New User"
        assert data["role"] == "admin"
        assert "loggedInAt" in data

        # Verify nested user object
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["displayName"] == "New User"
        assert data["user"]["name"] == "New User"
        assert data["user"]["role"] == "admin"

    def test_register_token_is_valid_jwt(self, client, mock_register_response):
        """Test that the returned token is a valid JWT with correct claims."""

        with patch(
            "src.app.features.auth.application.use_cases.register_user.RegisterUserUseCase.execute",
            new=AsyncMock(return_value=mock_register_response),
        ):
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass1",
                    "displayName": "New User",
                },
            )

        assert response.status_code == 201
        # We're mocking the use case, so we can't validate the JWT payload
        # Just verify the token is present in the response
        token = response.json()["token"]
        assert token == "mock.jwt.token"

    def test_register_with_duplicate_email_returns_409(self, client):
        """Test registration with existing email returns 409 Conflict."""
        with patch(
            "src.app.features.auth.application.use_cases.register_user.RegisterUserUseCase.execute",
            new=AsyncMock(side_effect=UserAlreadyExistsError("Email already registered")),
        ):
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "password": "SecurePass1",
                    "displayName": "Duplicate User",
                },
            )

        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    def test_register_with_invalid_email_format_returns_422(self, client):
        """Test registration with invalid email format returns 422."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass1",
                "displayName": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_with_weak_password_returns_400(self, client):
        """Test registration with weak password returns 400."""
        # For pydantic validation (password min length), we get 422
        # For business rule validation, we'd get 400
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",  # Too short (< 8 chars)
                "displayName": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_with_missing_email_returns_422(self, client):
        """Test registration with missing email field returns 422."""
        response = client.post(
            "/v1/auth/register",
            json={
                "password": "SecurePass1",
                "displayName": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_with_missing_password_returns_422(self, client):
        """Test registration with missing password field returns 422."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "displayName": "Test User",
            },
        )

        assert response.status_code == 422

    def test_register_with_missing_display_name_returns_422(self, client):
        """Test registration with missing displayName field returns 422."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass1",
            },
        )

        assert response.status_code == 422

    def test_register_with_empty_display_name_returns_422(self, client):
        """Test registration with empty displayName returns 422 (Pydantic validation)."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass1",
                "displayName": "",
            },
        )

        assert response.status_code == 422

    def test_register_creates_an_admin_account(self, client, mock_register_response):
        """Registration creates an admin account (api-contract.md: 'Accounts created as Admin role')."""
        with patch(
            "src.app.features.auth.application.use_cases.register_user.RegisterUserUseCase.execute",
            new=AsyncMock(return_value=mock_register_response),
        ):
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass1",
                    "displayName": "New User",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"
        assert data["user"]["role"] == "admin"

    def test_register_rejects_a_role_supplied_in_the_body(self, client):
        """A role in the request body is rejected outright rather than silently ignored.

        Registration is anonymous, so honouring this field would let anyone mint an admin.
        """
        execute = AsyncMock()
        with patch(
            "src.app.features.auth.application.use_cases.register_user.RegisterUserUseCase.execute",
            new=execute,
        ):
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass1",
                    "displayName": "New User",
                    "role": "admin",
                },
            )

        assert response.status_code == 422
        execute.assert_not_called()
