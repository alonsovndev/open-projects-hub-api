"""
Integration tests for user profile endpoints.

Tests GET /v1/users/me/profile and PATCH /v1/users/me/profile.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.app import fastapi_app
from src.app.config.app_config import AppConfig
from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


@pytest.fixture
def client():
    return TestClient(fastapi_app)


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


@pytest.fixture
def mock_user_response():
    """Fixture for a user profile response."""
    return UserResponse(
        id="12345678-90ab-cdef-1234-567890abcdef", email="user@example.com", display_name="Test User", role="viewer"
    )


class TestGetUserProfileEndpoint:
    """Tests for GET /v1/users/me/profile endpoint."""

    def test_get_profile_success(self, client, viewer_token):
        """Test successful profile retrieval for authenticated user."""
        mock_user_response = UserResponse(
            id="12345678-90ab-cdef-1234-567890abcdef", email="user@example.com", display_name="Test User", role="viewer"
        )

        with patch(
            "src.app.features.user.application.use_cases.get_user_profile.GetUserProfileUseCase.execute",
            new=AsyncMock(return_value=mock_user_response),
        ):
            response = client.get("/v1/users/me/profile", headers={"Authorization": f"Bearer {viewer_token}"})

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "12345678-90ab-cdef-1234-567890abcdef"
        assert data["email"] == "user@example.com"
        assert data["displayName"] == "Test User"
        assert data["role"] == "viewer"

    def test_get_profile_unauthorized_without_token(self, client):
        """Test that GET /profile requires authentication."""
        response = client.get("/v1/users/me/profile")

        assert response.status_code == 403  # HTTPBearer returns 403 when missing

    def test_get_profile_not_found(self, client, viewer_token):
        """Test that 404 is returned when user doesn't exist."""
        with patch(
            "src.app.features.user.application.use_cases.get_user_profile.GetUserProfileUseCase.execute",
            new=AsyncMock(side_effect=UserNotFoundException("12345678-90ab-cdef-1234-567890abcdef")),
        ):
            response = client.get("/v1/users/me/profile", headers={"Authorization": f"Bearer {viewer_token}"})

        assert response.status_code == 404


class TestUpdateUserProfileEndpoint:
    """Tests for PATCH /v1/users/me/profile endpoint."""

    def test_update_profile_success(self, client, viewer_token):
        """Test successful profile update."""
        updated_response = UserResponse(
            id="12345678-90ab-cdef-1234-567890abcdef",
            email="user@example.com",
            display_name="Updated Name",
            role="viewer",
        )

        with patch(
            "src.app.features.user.application.use_cases.update_user_profile.UpdateUserProfileUseCase.execute",
            new=AsyncMock(return_value=updated_response),
        ):
            response = client.patch(
                "/v1/users/me/profile",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"displayName": "Updated Name"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["displayName"] == "Updated Name"
        assert data["email"] == "user@example.com"
        assert data["role"] == "viewer"

    def test_update_profile_unauthorized_without_token(self, client):
        """Test that PATCH /profile requires authentication."""
        response = client.patch("/v1/users/me/profile", json={"displayName": "New Name"})

        assert response.status_code == 403

    def test_update_profile_empty_display_name_returns_400(self, client, viewer_token):
        """Test that empty display name returns 400."""
        with patch(
            "src.app.features.user.application.use_cases.update_user_profile.UpdateUserProfileUseCase.execute",
            new=AsyncMock(side_effect=ValueError("Display name cannot be empty")),
        ):
            response = client.patch(
                "/v1/users/me/profile", headers={"Authorization": f"Bearer {viewer_token}"}, json={"displayName": ""}
            )

        assert response.status_code == 400
        assert "Display name cannot be empty" in response.json()["detail"]

    def test_update_profile_too_long_display_name_returns_400(self, client, viewer_token):
        """Test that display name exceeding max length returns 400."""
        long_name = "a" * 256

        with patch(
            "src.app.features.user.application.use_cases.update_user_profile.UpdateUserProfileUseCase.execute",
            new=AsyncMock(side_effect=ValueError("Display name must not exceed 255 characters")),
        ):
            response = client.patch(
                "/v1/users/me/profile",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"displayName": long_name},
            )

        assert response.status_code == 400
        assert "255 characters" in response.json()["detail"]

    def test_update_profile_not_found(self, client, viewer_token):
        """Test that 404 is returned when user doesn't exist."""
        with patch(
            "src.app.features.user.application.use_cases.update_user_profile.UpdateUserProfileUseCase.execute",
            new=AsyncMock(side_effect=UserNotFoundException("12345678-90ab-cdef-1234-567890abcdef")),
        ):
            response = client.patch(
                "/v1/users/me/profile",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"displayName": "New Name"},
            )

        assert response.status_code == 404

    def test_update_profile_uses_camel_case(self, client, viewer_token):
        """Test that API accepts camelCase field names."""
        updated_response = UserResponse(
            id="12345678-90ab-cdef-1234-567890abcdef",
            email="user@example.com",
            display_name="Camel Case Test",
            role="viewer",
        )

        with patch(
            "src.app.features.user.application.use_cases.update_user_profile.UpdateUserProfileUseCase.execute",
            new=AsyncMock(return_value=updated_response),
        ):
            response = client.patch(
                "/v1/users/me/profile",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"displayName": "Camel Case Test"},  # camelCase
            )

        assert response.status_code == 200
        data = response.json()
        assert data["displayName"] == "Camel Case Test"  # Response is also camelCase
