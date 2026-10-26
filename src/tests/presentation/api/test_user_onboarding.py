"""
API tests for PATCH /v1/users/me/onboarding (F-005).
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.app.config.app_config import AppConfig
from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


USE_CASE_EXECUTE = (
    "src.app.features.user.application.use_cases.update_user_onboarding.UpdateUserOnboardingUseCase.execute"
)


@pytest.fixture
def admin_token():
    config = AppConfig.instance()
    jwt_handler = JWTHandler(
        secret_key=config.get_config("jwt.secret_key"), expiration_minutes=60, validate_secret=False
    )
    return jwt_handler.create_access_token(
        user_id="12345678-90ab-cdef-1234-567890abcdef",
        email="admin@example.com",
        role="admin",
        workspace_id="550e8400-e29b-41d4-a716-4466554400ff",
    )


def build_response(onboarding_completed: bool) -> UserResponse:
    return UserResponse(
        id="12345678-90ab-cdef-1234-567890abcdef",
        email="admin@example.com",
        display_name="Admin",
        role="admin",
        onboarding_completed=onboarding_completed,
    )


class TestUpdateOnboardingEndpoint:
    def test_dismiss_returns_completed_flag_in_camel_case(self, client, admin_token):
        execute = AsyncMock(return_value=build_response(True))

        with patch(USE_CASE_EXECUTE, new=execute):
            response = client.patch(
                "/v1/users/me/onboarding",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"completed": True},
            )

        assert response.status_code == 200
        assert response.json()["onboardingCompleted"] is True
        execute.assert_awaited_once_with("12345678-90ab-cdef-1234-567890abcdef", True)

    def test_reset_returns_not_completed(self, client, admin_token):
        with patch(USE_CASE_EXECUTE, new=AsyncMock(return_value=build_response(False))):
            response = client.patch(
                "/v1/users/me/onboarding",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"completed": False},
            )

        assert response.status_code == 200
        assert response.json()["onboardingCompleted"] is False

    def test_requires_authentication(self, client):
        response = client.patch("/v1/users/me/onboarding", json={"completed": True})

        assert response.status_code == 401

    def test_rejects_a_body_without_completed(self, client, admin_token):
        response = client.patch(
            "/v1/users/me/onboarding",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )

        assert response.status_code == 422

    def test_unknown_user_returns_404(self, client, admin_token):
        with patch(
            USE_CASE_EXECUTE,
            new=AsyncMock(side_effect=UserNotFoundError("12345678-90ab-cdef-1234-567890abcdef")),
        ):
            response = client.patch(
                "/v1/users/me/onboarding",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"completed": True},
            )

        assert response.status_code == 404
