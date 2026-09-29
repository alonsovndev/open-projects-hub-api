from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.app.features.auth.application.dtos.auth_dto import RegisterResponse
from src.app.features.auth.domain.exceptions.auth_exceptions import RegistrationClosedError
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError


@pytest.fixture
def mock_register_response():
    """Fixture for a registration awaiting email verification."""
    return RegisterResponse(
        email="ne***@example.com",
        code_expires_at=(datetime.now(tz=UTC) + timedelta(minutes=5)).isoformat(),
    )


class TestRegisterEndpoint:
    def test_register_success_returns_201_pending_verification(self, client, mock_register_response):
        """Registration returns 201 with the next step and no tokens (FR-008-06)."""
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
        assert data == {
            "email": "ne***@example.com",
            "verificationRequired": True,
            "nextStep": "verify-email",
            "codeExpiresAt": mock_register_response.code_expires_at,
        }
        assert "token" not in data
        assert "accessToken" not in data

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

    def test_register_returns_403_once_the_instance_has_an_account(self, client):
        """Registration bootstraps the first Admin; afterwards it is closed, not merely rate-limited."""
        with patch(
            "src.app.features.auth.application.use_cases.register_user.RegisterUserUseCase.execute",
            new=AsyncMock(side_effect=RegistrationClosedError()),
        ):
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "second@example.com",
                    "password": "SecurePass1",
                    "displayName": "Second Person",
                },
            )

        assert response.status_code == 403
        assert "Registration is closed" in response.json()["detail"]
