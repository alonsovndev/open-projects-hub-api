"""
Integration tests for user password change endpoint.

Tests POST /v1/user/password.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.app.app import fastApiApp
from src.app.config.app_config import AppConfig
from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
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
def viewer_token(app_jwt_handler):
    """Generate valid viewer JWT token."""
    return app_jwt_handler.create_access_token(
        user_id="12345678-90ab-cdef-1234-567890abcdef",
        email="user@example.com",
        role="viewer",
    )


class TestChangePasswordEndpoint:
    """Tests for POST /v1/user/password endpoint."""

    def test_change_password_success(self, client, viewer_token):
        """Test successful password change."""
        with patch(
            "src.app.features.user.application.use_cases.change_password.ChangePasswordUseCase.execute",
            new=AsyncMock(return_value=None)
        ):
            response = client.post(
                "/v1/user/password",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "currentPassword": "OldPass123",
                    "newPassword": "NewPass456"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password changed successfully"

    def test_change_password_unauthorized_without_token(self, client):
        """Test that POST /password requires authentication."""
        response = client.post(
            "/v1/user/password",
            json={
                "currentPassword": "OldPass123",
                "newPassword": "NewPass456"
            }
        )

        assert response.status_code == 403  # HTTPBearer returns 403 when missing

    def test_change_password_incorrect_current_password(self, client, viewer_token):
        """Test that incorrect current password returns 400."""
        with patch(
            "src.app.features.user.application.use_cases.change_password.ChangePasswordUseCase.execute",
            new=AsyncMock(side_effect=ValueError("Current password is incorrect"))
        ):
            response = client.post(
                "/v1/user/password",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "currentPassword": "WrongPass",
                    "newPassword": "NewPass456"
                }
            )

        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    def test_change_password_weak_new_password(self, client, viewer_token):
        """Test that weak new password returns 400."""
        with patch(
            "src.app.features.user.application.use_cases.change_password.ChangePasswordUseCase.execute",
            new=AsyncMock(side_effect=ValueError("Password must be at least 8 characters"))
        ):
            response = client.post(
                "/v1/user/password",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "currentPassword": "OldPass123",
                    "newPassword": "Short1"
                }
            )

        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    def test_change_password_missing_letter(self, client, viewer_token):
        """Test that password without letter returns 400."""
        with patch(
            "src.app.features.user.application.use_cases.change_password.ChangePasswordUseCase.execute",
            new=AsyncMock(side_effect=ValueError("Password must contain at least one letter"))
        ):
            response = client.post(
                "/v1/user/password",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "currentPassword": "OldPass123",
                    "newPassword": "12345678"
                }
            )

        assert response.status_code == 400
        assert "letter" in response.json()["detail"]

    def test_change_password_missing_digit(self, client, viewer_token):
        """Test that password without digit returns 400."""
        with patch(
            "src.app.features.user.application.use_cases.change_password.ChangePasswordUseCase.execute",
            new=AsyncMock(side_effect=ValueError("Password must contain at least one digit"))
        ):
            response = client.post(
                "/v1/user/password",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "currentPassword": "OldPass123",
                    "newPassword": "NoDigitsHere"
                }
            )

        assert response.status_code == 400
        assert "digit" in response.json()["detail"]

    def test_change_password_user_not_found(self, client, viewer_token):
        """Test that 404 is returned when user doesn't exist."""
        with patch(
            "src.app.features.user.application.use_cases.change_password.ChangePasswordUseCase.execute",
            new=AsyncMock(side_effect=UserNotFoundException("12345678-90ab-cdef-1234-567890abcdef"))
        ):
            response = client.post(
                "/v1/user/password",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "currentPassword": "OldPass123",
                    "newPassword": "NewPass456"
                }
            )

        assert response.status_code == 404

    def test_change_password_uses_camel_case(self, client, viewer_token):
        """Test that API accepts camelCase field names."""
        with patch(
            "src.app.features.user.application.use_cases.change_password.ChangePasswordUseCase.execute",
            new=AsyncMock(return_value=None)
        ):
            response = client.post(
                "/v1/user/password",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={
                    "currentPassword": "OldPass123",  # camelCase
                    "newPassword": "NewPass456"       # camelCase
                }
            )

        assert response.status_code == 200
