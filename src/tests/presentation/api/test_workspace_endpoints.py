"""API tests for PATCH /v1/workspaces/me."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config.app_config import AppConfig
from src.app.features.workspaces.application.dtos.workspace_dto import WorkspaceResponse
from src.app.features.workspaces.domain.exceptions.workspace_exceptions import WorkspaceNotFoundError
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


WORKSPACE_ID = "550e8400-e29b-41d4-a716-4466554400ff"
EXECUTE_PATH = "src.app.features.workspaces.application.use_cases.update_workspace.UpdateWorkspaceUseCase.execute"


def _token(role: str) -> str:
    secret_key = AppConfig.instance().get_config("jwt.secret_key")
    handler = JWTHandler(secret_key=secret_key, expiration_minutes=60, validate_secret=False)
    return handler.create_access_token(
        user_id="550e8400-e29b-41d4-a716-446655440001",
        email=f"{role}@example.com",
        role=role,
        workspace_id=WORKSPACE_ID,
    )


class TestUpdateWorkspaceEndpoint:
    def test_admin_renames_workspace(self, client: TestClient):
        with patch(EXECUTE_PATH, new=AsyncMock(return_value=WorkspaceResponse(id=WORKSPACE_ID, name="New"))):
            response = client.patch(
                "/v1/workspaces/me", json={"name": "New"}, headers={"Authorization": f"Bearer {_token('admin')}"}
            )

        assert response.status_code == 200
        assert response.json() == {"id": WORKSPACE_ID, "name": "New"}

    @pytest.mark.parametrize("role", ["member"])
    def test_non_admin_is_forbidden(self, client: TestClient, role: str):
        response = client.patch(
            "/v1/workspaces/me", json={"name": "New"}, headers={"Authorization": f"Bearer {_token(role)}"}
        )

        assert response.status_code == 403

    def test_requires_authentication(self, client: TestClient):
        assert client.patch("/v1/workspaces/me", json={"name": "New"}).status_code == 401

    @pytest.mark.parametrize("invalid_name", ["", "   ", "x" * 101])
    def test_invalid_name_returns_422(self, client: TestClient, invalid_name: str):
        response = client.patch(
            "/v1/workspaces/me", json={"name": invalid_name}, headers={"Authorization": f"Bearer {_token('admin')}"}
        )

        assert response.status_code == 422

    def test_missing_workspace_returns_404(self, client: TestClient):
        with patch(EXECUTE_PATH, new=AsyncMock(side_effect=WorkspaceNotFoundError(WORKSPACE_ID))):
            response = client.patch(
                "/v1/workspaces/me", json={"name": "New"}, headers={"Authorization": f"Bearer {_token('admin')}"}
            )

        assert response.status_code == 404
