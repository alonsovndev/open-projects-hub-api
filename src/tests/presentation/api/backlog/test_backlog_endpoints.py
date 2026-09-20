"""Integration tests for the backlog view and Markdown export endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config.app_config import AppConfig
from src.app.features.backlog.application.dtos.backlog_dto import BacklogStoryResponse, MarkdownExport
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


PROJECT_ID = "550e8400-e29b-41d4-a716-446655440010"
BACKLOG_URL = f"/v1/projects/{PROJECT_ID}/backlog"
EXPORT_URL = f"/v1/projects/{PROJECT_ID}/exports/markdown"

BACKLOG_USE_CASE = "src.app.features.backlog.application.use_cases.get_project_backlog.GetProjectBacklogUseCase.execute"
EXPORT_USE_CASE = (
    "src.app.features.backlog.application.use_cases.export_backlog_markdown.ExportBacklogMarkdownUseCase.execute"
)


@pytest.fixture
def app_jwt_handler():
    """JWT handler using the app's configured secret key."""
    config = AppConfig.instance()
    secret_key = config.get_config("jwt.secret_key")
    return JWTHandler(secret_key=secret_key, expiration_minutes=60, validate_secret=False)


@pytest.fixture
def admin_token(app_jwt_handler):
    """Generate admin JWT token for tests."""
    return app_jwt_handler.create_access_token(
        user_id="550e8400-e29b-41d4-a716-446655440001",
        email="admin@example.com",
        role="admin",
    )


@pytest.fixture
def viewer_token(app_jwt_handler):
    """Generate viewer JWT token for tests."""
    return app_jwt_handler.create_access_token(
        user_id="550e8400-e29b-41d4-a716-446655440002",
        email="viewer@example.com",
        role="viewer",
    )


@pytest.fixture
def mock_backlog_page():
    """A one-story backlog page."""
    return PaginatedResponse[BacklogStoryResponse](
        total=1,
        page=1,
        per_page=50,
        items=[
            BacklogStoryResponse(
                id="550e8400-e29b-41d4-a716-446655440100",
                title="User login",
                description="As a user I want to log in",
                acceptance_criteria=["User can enter credentials"],
                status="todo",
                priority="high",
                points=3,
                created_at="2026-05-09T12:00:00",
                updated_at="2026-05-09T12:00:00",
            )
        ],
    )


@pytest.fixture
def mock_export():
    """A rendered export with one story."""
    return MarkdownExport(
        filename="acme-portal-backlog-2026-09-20.md",
        content="# Acme Portal — Requirements Backlog\n",
        story_count=1,
    )


class TestGetProjectBacklogEndpoint:
    """Test GET /v1/projects/{project_id}/backlog."""

    def test_backlog_returns_stories_with_acceptance_criteria(self, client: TestClient, admin_token, mock_backlog_page):
        """Test that criteria are serialized in camelCase for the client."""
        with patch(BACKLOG_USE_CASE, new=AsyncMock(return_value=mock_backlog_page)):
            response = client.get(BACKLOG_URL, headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["acceptanceCriteria"] == ["User can enter credentials"]

    def test_backlog_is_readable_by_a_viewer(self, client: TestClient, viewer_token, mock_backlog_page):
        """A Viewer's whole purpose is reading the approved backlog."""
        with patch(BACKLOG_USE_CASE, new=AsyncMock(return_value=mock_backlog_page)):
            response = client.get(BACKLOG_URL, headers={"Authorization": f"Bearer {viewer_token}"})

        assert response.status_code == 200

    def test_backlog_requires_a_token(self, client: TestClient):
        """Test that an anonymous caller is refused with 401, not 403."""
        response = client.get(BACKLOG_URL)

        assert response.status_code == 401

    def test_backlog_rejects_an_invalid_token(self, client: TestClient):
        """Test that a forged token is refused."""
        response = client.get(BACKLOG_URL, headers={"Authorization": "Bearer not-a-real-token"})

        assert response.status_code == 401

    def test_unknown_project_returns_404(self, client: TestClient, admin_token):
        """Test that a missing project is reported as 404."""
        with patch(BACKLOG_USE_CASE, new=AsyncMock(side_effect=ProjectNotFoundError(PROJECT_ID))):
            response = client.get(BACKLOG_URL, headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 404


class TestExportBacklogMarkdownEndpoint:
    """Test POST /v1/projects/{project_id}/exports/markdown."""

    def test_export_returns_a_markdown_attachment(self, client: TestClient, admin_token, mock_export):
        """Test that the response is a downloadable Markdown file."""
        with patch(EXPORT_USE_CASE, new=AsyncMock(return_value=mock_export)):
            response = client.post(EXPORT_URL, headers={"Authorization": f"Bearer {admin_token}"}, json={})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/markdown")
        assert response.headers["content-disposition"] == ('attachment; filename="acme-portal-backlog-2026-09-20.md"')
        assert response.headers["x-export-story-count"] == "1"
        assert "x-export-warning" not in response.headers
        assert response.text.startswith("# Acme Portal")

    def test_export_without_a_body_exports_everything(self, client: TestClient, admin_token, mock_export):
        """Test that an absent request body is accepted as an unscoped export."""
        with patch(EXPORT_USE_CASE, new=AsyncMock(return_value=mock_export)) as mocked:
            response = client.post(EXPORT_URL, headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        scope = mocked.await_args.kwargs["scope"]
        assert scope.status is None
        assert scope.date_from is None

    def test_empty_export_warns_but_still_returns_the_file(self, client: TestClient, admin_token):
        """FR-004-06: an empty scope is warned about, not refused."""
        empty = MarkdownExport(
            filename="acme-portal-backlog-2026-09-20.md",
            content="# Acme Portal — Requirements Backlog\n\n_No approved stories match this scope._\n",
            story_count=0,
        )

        with patch(EXPORT_USE_CASE, new=AsyncMock(return_value=empty)):
            response = client.post(EXPORT_URL, headers={"Authorization": f"Bearer {admin_token}"}, json={})

        assert response.status_code == 200
        assert response.headers["x-export-story-count"] == "0"
        assert response.headers["x-export-warning"] == "No approved stories match this scope."
        assert "No approved stories" in response.text

    def test_export_exposes_its_headers_to_the_browser(self, client: TestClient, admin_token, mock_export):
        """The web client reads the filename and count, which CORS hides by default."""
        with patch(EXPORT_USE_CASE, new=AsyncMock(return_value=mock_export)):
            response = client.post(EXPORT_URL, headers={"Authorization": f"Bearer {admin_token}"}, json={})

        exposed = response.headers["access-control-expose-headers"]
        assert "Content-Disposition" in exposed
        assert "X-Export-Story-Count" in exposed
        assert "X-Export-Warning" in exposed

    def test_export_scope_reaches_the_use_case(self, client: TestClient, admin_token, mock_export):
        """Test that status and date filters are parsed from camelCase."""
        with patch(EXPORT_USE_CASE, new=AsyncMock(return_value=mock_export)) as mocked:
            response = client.post(
                EXPORT_URL,
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"status": "done", "dateFrom": "2026-01-01", "dateTo": "2026-06-30"},
            )

        assert response.status_code == 200
        scope = mocked.await_args.kwargs["scope"]
        assert scope.status.value == "done"
        assert scope.date_from.isoformat() == "2026-01-01"
        assert scope.date_to.isoformat() == "2026-06-30"

    def test_export_rejects_an_unknown_scope_field(self, client: TestClient, admin_token):
        """Test that a misspelled filter is refused rather than silently ignored."""
        response = client.post(
            EXPORT_URL,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"statuss": "done"},
        )

        assert response.status_code == 422

    def test_export_rejects_an_inverted_date_range(self, client: TestClient, admin_token):
        """Test that an inverted range is refused rather than exporting nothing."""
        response = client.post(
            EXPORT_URL,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"dateFrom": "2026-06-30", "dateTo": "2026-01-01"},
        )

        assert response.status_code == 422

    def test_unknown_project_returns_404(self, client: TestClient, admin_token):
        """Test that exporting a missing project is reported as 404."""
        with patch(EXPORT_USE_CASE, new=AsyncMock(side_effect=ProjectNotFoundError(PROJECT_ID))):
            response = client.post(EXPORT_URL, headers={"Authorization": f"Bearer {admin_token}"}, json={})

        assert response.status_code == 404


class TestExportRoleBoundary:
    """FR-004-05: a Viewer may read the backlog but never take it away.

    These deliberately do not patch the use case: if the guard were removed, the request
    would reach the real use case and fail some other way instead of passing silently.
    """

    def test_export_is_forbidden_for_a_viewer(self, client: TestClient, viewer_token):
        """Test that a Viewer's export attempt is refused with 403."""
        response = client.post(EXPORT_URL, headers={"Authorization": f"Bearer {viewer_token}"}, json={})

        assert response.status_code == 403

    def test_export_requires_a_token(self, client: TestClient):
        """Test that an anonymous export attempt is refused with 401."""
        response = client.post(EXPORT_URL, json={})

        assert response.status_code == 401

    def test_export_rejects_an_invalid_token(self, client: TestClient):
        """Test that a forged token cannot export."""
        response = client.post(
            EXPORT_URL,
            headers={"Authorization": "Bearer not-a-real-token"},
            json={},
        )

        assert response.status_code == 401
