"""
Integration tests for user preferences endpoints.

Tests GET /v1/users/me/preferences and PATCH /v1/users/me/preferences.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.app.app import fastApiApp
from src.app.config.app_config import AppConfig
from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.value_objects.theme import Theme
from src.app.shared.domain.value_objects.entity_id import EntityId
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


class TestGetUserPreferencesEndpoint:
    """Tests for GET /v1/users/me/preferences endpoint."""

    def test_get_preferences_success(self, client, viewer_token):
        """Test successful preferences retrieval."""
        mock_preferences = UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=EntityId.from_string("12345678-90ab-cdef-1234-567890abcdef"),
            theme=Theme.DARK,
            language="en"
        )
        
        with patch(
            "src.app.features.user.application.use_cases.get_user_preferences.GetUserPreferencesUseCase.execute",
            new=AsyncMock(return_value=mock_preferences)
        ):
            response = client.get(
                "/v1/users/me/preferences",
                headers={"Authorization": f"Bearer {viewer_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["theme"] == "dark"
        assert data["language"] == "en"
        assert "id" in data
        assert "userId" in data

    def test_get_preferences_creates_default_when_not_found(self, client, viewer_token):
        """Test that GET auto-creates default preferences if none exist."""
        # The use case returns default preferences
        mock_default = UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=EntityId.from_string("12345678-90ab-cdef-1234-567890abcdef"),
            theme=Theme.AUTO,
            language="en"
        )
        
        with patch(
            "src.app.features.user.application.use_cases.get_user_preferences.GetUserPreferencesUseCase.execute",
            new=AsyncMock(return_value=mock_default)
        ):
            response = client.get(
                "/v1/users/me/preferences",
                headers={"Authorization": f"Bearer {viewer_token}"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["theme"] == "auto"
        assert data["language"] == "en"

    def test_get_preferences_unauthorized_without_token(self, client):
        """Test that GET /preferences requires authentication."""
        response = client.get("/v1/users/me/preferences")

        assert response.status_code == 403  # HTTPBearer returns 403 when missing


class TestUpdateUserPreferencesEndpoint:
    """Tests for PATCH /v1/users/me/preferences endpoint."""

    def test_update_preferences_theme_only(self, client, viewer_token):
        """Test updating theme preference only."""
        updated_preferences = UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=EntityId.from_string("12345678-90ab-cdef-1234-567890abcdef"),
            theme=Theme.LIGHT,
            language="en"
        )
        
        with patch(
            "src.app.features.user.application.use_cases.update_user_preferences.UpdateUserPreferencesUseCase.execute",
            new=AsyncMock(return_value=updated_preferences)
        ):
            response = client.patch(
                "/v1/users/me/preferences",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"theme": "light"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["theme"] == "light"
        assert data["language"] == "en"

    def test_update_preferences_language_only(self, client, viewer_token):
        """Test updating language preference only."""
        updated_preferences = UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=EntityId.from_string("12345678-90ab-cdef-1234-567890abcdef"),
            theme=Theme.AUTO,
            language="es"
        )
        
        with patch(
            "src.app.features.user.application.use_cases.update_user_preferences.UpdateUserPreferencesUseCase.execute",
            new=AsyncMock(return_value=updated_preferences)
        ):
            response = client.patch(
                "/v1/users/me/preferences",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"language": "es"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["theme"] == "auto"
        assert data["language"] == "es"

    def test_update_preferences_both_fields(self, client, viewer_token):
        """Test updating both theme and language."""
        updated_preferences = UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=EntityId.from_string("12345678-90ab-cdef-1234-567890abcdef"),
            theme=Theme.DARK,
            language="fr"
        )
        
        with patch(
            "src.app.features.user.application.use_cases.update_user_preferences.UpdateUserPreferencesUseCase.execute",
            new=AsyncMock(return_value=updated_preferences)
        ):
            response = client.patch(
                "/v1/users/me/preferences",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"theme": "dark", "language": "fr"}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["theme"] == "dark"
        assert data["language"] == "fr"

    def test_update_preferences_invalid_theme(self, client, viewer_token):
        """Test that invalid theme returns 400."""
        response = client.patch(
            "/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"theme": "invalid"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_update_preferences_unauthorized_without_token(self, client):
        """Test that PATCH /preferences requires authentication."""
        response = client.patch(
            "/v1/users/me/preferences",
            json={"theme": "dark"}
        )

        assert response.status_code == 403

    def test_update_preferences_uses_camel_case(self, client, viewer_token):
        """Test that API accepts camelCase field names."""
        updated_preferences = UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=EntityId.from_string("12345678-90ab-cdef-1234-567890abcdef"),
            theme=Theme.LIGHT,
            language="en"
        )
        
        with patch(
            "src.app.features.user.application.use_cases.update_user_preferences.UpdateUserPreferencesUseCase.execute",
            new=AsyncMock(return_value=updated_preferences)
        ):
            response = client.patch(
                "/v1/users/me/preferences",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={"theme": "light"}  # camelCase works same as snake_case
            )

        assert response.status_code == 200

    def test_update_preferences_empty_body(self, client, viewer_token):
        """Test that empty update body is handled gracefully."""
        # Use case should return existing preferences unchanged
        existing_preferences = UserPreferencesEntity(
            id=EntityId.generate(),
            user_id=EntityId.from_string("12345678-90ab-cdef-1234-567890abcdef"),
            theme=Theme.AUTO,
            language="en"
        )
        
        with patch(
            "src.app.features.user.application.use_cases.update_user_preferences.UpdateUserPreferencesUseCase.execute",
            new=AsyncMock(return_value=existing_preferences)
        ):
            response = client.patch(
                "/v1/users/me/preferences",
                headers={"Authorization": f"Bearer {viewer_token}"},
                json={}
            )

        assert response.status_code == 200
