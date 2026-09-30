"""Cross-workspace isolation at the route layer.

Each route that names a record by id must (a) hand the use case the workspace from the
caller's token, never from the path or body, and (b) answer a record the use case cannot
see in that workspace with 404 — not 403, which would confirm the id exists elsewhere.
The repository-level filters that make the use case "not see" it are covered by the
SQL predicate tests and the port guard.
"""

from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from src.app.config.app_config import AppConfig
from src.app.features.clients.domain.exceptions.client_exceptions import ClientNotFoundError
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.refinement.domain.exceptions.refinement_exceptions import StoryDraftNotFoundError
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.shared.application.request_context import RequestContext
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


WORKSPACE_A = str(uuid4())
RECORD_ID = str(uuid4())
USE_CASES = "src.app.features"

# (method, path, use case execute target, what the use case raises when the record is not in the workspace)
ID_ROUTES = [
    (
        "GET",
        f"/v1/clients/{RECORD_ID}",
        "clients.application.use_cases.get_client_by_id.GetClientByIdUseCase",
        ClientNotFoundError(RECORD_ID),
    ),
    (
        "PATCH",
        f"/v1/clients/{RECORD_ID}",
        "clients.application.use_cases.update_client.UpdateClientUseCase",
        ClientNotFoundError(RECORD_ID),
    ),
    (
        "DELETE",
        f"/v1/clients/{RECORD_ID}",
        "clients.application.use_cases.delete_client.DeleteClientUseCase",
        ClientNotFoundError(RECORD_ID),
    ),
    (
        "GET",
        f"/v1/projects/{RECORD_ID}",
        "projects.application.use_cases.get_project_by_id.GetProjectByIdUseCase",
        None,
    ),
    (
        "PATCH",
        f"/v1/projects/{RECORD_ID}",
        "projects.application.use_cases.update_project.UpdateProjectUseCase",
        ProjectNotFoundError(RECORD_ID),
    ),
    (
        "DELETE",
        f"/v1/projects/{RECORD_ID}",
        "projects.application.use_cases.delete_project.DeleteProjectUseCase",
        ProjectNotFoundError(RECORD_ID),
    ),
    (
        "POST",
        f"/v1/projects/{RECORD_ID}/archive",
        "projects.application.use_cases.archive_project.ArchiveProjectUseCase",
        ProjectNotFoundError(RECORD_ID),
    ),
    (
        "POST",
        f"/v1/projects/{RECORD_ID}/reactivate",
        "projects.application.use_cases.reactivate_project.ReactivateProjectUseCase",
        ProjectNotFoundError(RECORD_ID),
    ),
    (
        "GET",
        f"/v1/projects/{RECORD_ID}/backlog",
        "backlog.application.use_cases.get_project_backlog.GetProjectBacklogUseCase",
        ProjectNotFoundError(RECORD_ID),
    ),
    (
        "POST",
        f"/v1/projects/{RECORD_ID}/exports/markdown",
        "backlog.application.use_cases.export_backlog_markdown.ExportBacklogMarkdownUseCase",
        ProjectNotFoundError(RECORD_ID),
    ),
    (
        "GET",
        f"/v1/stories/{RECORD_ID}",
        "stories.application.use_cases.get_story_by_id.GetStoryByIdUseCase",
        StoryNotFoundError(RECORD_ID),
    ),
    (
        "PATCH",
        f"/v1/stories/{RECORD_ID}",
        "stories.application.use_cases.update_story.UpdateStoryUseCase",
        StoryNotFoundError(RECORD_ID),
    ),
    (
        "DELETE",
        f"/v1/stories/{RECORD_ID}",
        "stories.application.use_cases.delete_story.DeleteStoryUseCase",
        StoryNotFoundError(RECORD_ID),
    ),
    (
        "POST",
        f"/v1/stories/{RECORD_ID}/assign",
        "stories.application.use_cases.assign_story.AssignStoryUseCase",
        StoryNotFoundError(RECORD_ID),
    ),
    (
        "PATCH",
        f"/v1/refinement/drafts/{RECORD_ID}",
        "refinement.application.use_cases.update_story_draft.UpdateStoryDraftUseCase",
        StoryDraftNotFoundError(RECORD_ID),
    ),
    (
        "DELETE",
        f"/v1/refinement/drafts/{RECORD_ID}",
        "refinement.application.use_cases.delete_story_draft.DeleteStoryDraftUseCase",
        StoryDraftNotFoundError(RECORD_ID),
    ),
    (
        "POST",
        f"/v1/refinement/drafts/{RECORD_ID}/approve",
        "refinement.application.use_cases.approve_draft.ApproveDraftUseCase",
        StoryDraftNotFoundError(RECORD_ID),
    ),
    (
        "GET",
        f"/v1/users/{RECORD_ID}",
        "user.application.use_cases.get_user_by_id.GetUserByIdUseCase",
        UserNotFoundError(RECORD_ID),
    ),
]

BODIES: dict[str, dict[str, Any]] = {
    "PATCH /v1/clients": {"name": "Acme"},
    "PATCH /v1/projects": {"name": "Renamed"},
    "PATCH /v1/stories": {"title": "Renamed"},
    "POST /v1/stories": {"userId": str(uuid4())},
    "PATCH /v1/refinement": {"title": "Renamed"},
    "POST /v1/projects": {},
}


def body_for(method: str, path: str) -> dict[str, Any] | None:
    for prefix, body in BODIES.items():
        verb, route = prefix.split(" ")
        if verb == method and path.startswith(route):
            return body
    return None


@pytest.fixture
def jwt_handler():
    secret_key = AppConfig.instance().get_config("jwt.secret_key")
    return JWTHandler(secret_key=secret_key, expiration_minutes=60, validate_secret=False)


def token_for(jwt_handler: JWTHandler, role: str, workspace_id: str | None = WORKSPACE_A) -> str:
    return jwt_handler.create_access_token(
        user_id=str(uuid4()), email=f"{role}@example.com", role=role, workspace_id=workspace_id
    )


def captured_context(call_args) -> RequestContext:
    args, kwargs = call_args
    return kwargs.get("ctx") or next(arg for arg in args if isinstance(arg, RequestContext))


class TestRecordsOfAnotherWorkspace:
    @pytest.mark.parametrize(("method", "path", "use_case", "not_found"), ID_ROUTES)
    def test_answer_404_with_the_workspace_taken_from_the_token(
        self, client, jwt_handler, method, path, use_case, not_found
    ):
        calls = []

        async def fake_execute(_self, *args, **kwargs):
            calls.append((args, kwargs))
            if not_found is None:
                return
            raise not_found

        with patch(f"{USE_CASES}.{use_case}.execute", new=fake_execute):
            response = client.request(
                method,
                path,
                json=body_for(method, path),
                headers={"Authorization": f"Bearer {token_for(jwt_handler, 'member')}"},
            )

        assert response.status_code == 404, response.text
        assert str(captured_context(calls[0]).workspace_id) == WORKSPACE_A


class TestTokenAndRoleBoundaries:
    def test_a_token_without_a_workspace_is_rejected(self, client, jwt_handler):
        """Tokens minted before workspaces existed must refresh, not fall through unscoped."""
        response = client.get(
            "/v1/projects", headers={"Authorization": f"Bearer {token_for(jwt_handler, 'admin', workspace_id=None)}"}
        )

        assert response.status_code == 401

    def test_a_viewer_cannot_write(self, client, jwt_handler):
        response = client.post(
            "/v1/clients",
            json={"name": "Acme"},
            headers={"Authorization": f"Bearer {token_for(jwt_handler, 'viewer')}"},
        )

        assert response.status_code == 403

    def test_a_member_cannot_add_users(self, client, jwt_handler):
        response = client.post(
            "/v1/users",
            json={"displayName": "Mate", "email": "mate@example.com", "password": "SecurePass123"},
            headers={"Authorization": f"Bearer {token_for(jwt_handler, 'member')}"},
        )

        assert response.status_code == 403

    def test_an_admin_cannot_create_another_admin(self, client, jwt_handler):
        response = client.post(
            "/v1/users",
            json={"displayName": "Boss", "email": "boss@example.com", "password": "SecurePass123", "role": "admin"},
            headers={"Authorization": f"Bearer {token_for(jwt_handler, 'admin')}"},
        )

        assert response.status_code == 422
