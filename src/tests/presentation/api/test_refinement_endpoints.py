"""Integration tests for refinement endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config.app_config import AppConfig
from src.app.features.refinement.application.dtos.refinement_dto import GeneratedStoryResponse, GenerateStoriesResponse
from src.app.features.refinement.domain.exceptions.refinement_exceptions import RefinementFailedError
from src.app.features.refinement.domain.value_objects.refinement_failure_class import RefinementFailureClass
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


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
        workspace_id="550e8400-e29b-41d4-a716-4466554400ff",
    )


@pytest.fixture
def mock_story_response():
    """Create a mock story response DTO."""
    return StoryResponse(
        id="550e8400-e29b-41d4-a716-446655440100",
        title="Test Story",
        description="Test description",
        acceptance_criteria=[],
        project_id="550e8400-e29b-41d4-a716-446655440001",
        created_by="550e8400-e29b-41d4-a716-446655440001",
        assigned_to=None,
        status="todo",
        priority="medium",
        points=None,
        created_at="2026-05-21T12:00:00",
        updated_at="2026-05-21T12:00:00",
    )


@pytest.mark.integration
class TestGenerateStoriesEndpoint:
    """Test POST /v1/refinement/generate-stories endpoint."""

    def test_generate_stories_success(self, client: TestClient, admin_token: str):
        """Test generating stories returns 200."""
        mock_response = GenerateStoriesResponse(
            stories=[
                GeneratedStoryResponse(
                    title="Generated Story",
                    description="Generated description",
                    acceptance_criteria=["Criterion 1"],
                ),
            ],
            raw_notes="Some raw notes",
        )

        with patch(
            "src.app.features.refinement.application.use_cases.generate_stories_from_notes.GenerateStoriesFromNotesUseCase.execute",
            new=AsyncMock(return_value=mock_response),
        ):
            response = client.post(
                "/v1/refinement/generate-stories",
                json={
                    "projectId": "550e8400-e29b-41d4-a716-446655440001",
                    "rawNotes": "Some raw notes that are long enough to pass validation",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["stories"]) == 1
        assert data["stories"][0]["title"] == "Generated Story"
        assert data["rawNotes"] == "Some raw notes"

    def test_generate_stories_unauthorized_without_token(self, client: TestClient):
        """Test generating stories without token returns 401."""
        response = client.post(
            "/v1/refinement/generate-stories",
            json={
                "projectId": "550e8400-e29b-41d4-a716-446655440001",
                "rawNotes": "Some raw notes that are long enough",
            },
        )

        assert response.status_code == 401

    def test_generate_stories_validation_error_empty_notes(self, client: TestClient, admin_token: str):
        """Test generating stories with empty notes returns 422."""
        response = client.post(
            "/v1/refinement/generate-stories",
            json={
                "projectId": "550e8400-e29b-41d4-a716-446655440001",
                "rawNotes": "",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_generate_stories_validation_error_short_notes(self, client: TestClient, admin_token: str):
        """Test generating stories with short notes returns 422."""
        response = client.post(
            "/v1/refinement/generate-stories",
            json={
                "projectId": "550e8400-e29b-41d4-a716-446655440001",
                "rawNotes": "Too short",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_generate_stories_camel_case_serialization(self, client: TestClient, admin_token: str):
        """Test that request and response use camelCase."""
        mock_response = GenerateStoriesResponse(
            stories=[
                GeneratedStoryResponse(
                    title="Story",
                    description="Desc",
                    acceptance_criteria=["Crit"],
                ),
            ],
            raw_notes="Notes",
        )

        with patch(
            "src.app.features.refinement.application.use_cases.generate_stories_from_notes.GenerateStoriesFromNotesUseCase.execute",
            new=AsyncMock(return_value=mock_response),
        ):
            response = client.post(
                "/v1/refinement/generate-stories",
                json={
                    "projectId": "550e8400-e29b-41d4-a716-446655440001",
                    "rawNotes": "Some raw notes that are long enough to pass validation",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "stories" in data
        assert "rawNotes" in data
        assert "acceptanceCriteria" in data["stories"][0]


APPROVE_BODY = {
    "projectId": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Refined Story",
    "description": "Refined description",
    "acceptanceCriteria": ["Criterion 1"],
}


@pytest.mark.integration
class TestApproveStoryEndpoint:
    """Test POST /v1/refinement/approve-story endpoint."""

    def test_approve_story_success(self, client: TestClient, admin_token: str, mock_story_response):
        with patch(
            "src.app.features.refinement.application.use_cases.approve_story.ApproveStoryUseCase.execute",
            new=AsyncMock(return_value=mock_story_response),
        ) as execute:
            response = client.post(
                "/v1/refinement/approve-story",
                json=APPROVE_BODY,
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440100"
        assert data["title"] == "Test Story"
        request = execute.call_args.kwargs["request"]
        assert request.title == "Refined Story"
        assert request.acceptance_criteria == ["Criterion 1"]

    def test_approve_story_project_not_found(self, client: TestClient, admin_token: str):
        with patch(
            "src.app.features.refinement.application.use_cases.approve_story.ApproveStoryUseCase.execute",
            new=AsyncMock(side_effect=NotFoundError("Project", APPROVE_BODY["projectId"])),
        ):
            response = client.post(
                "/v1/refinement/approve-story",
                json=APPROVE_BODY,
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_approve_story_validation_error_empty_title(self, client: TestClient, admin_token: str):
        response = client.post(
            "/v1/refinement/approve-story",
            json={**APPROVE_BODY, "title": ""},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_approve_story_unauthorized_without_token(self, client: TestClient):
        response = client.post("/v1/refinement/approve-story", json=APPROVE_BODY)

        assert response.status_code == 401

    def test_removed_draft_routes_no_longer_exist(self, client: TestClient, admin_token: str):
        draft_url = "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100"
        headers = {"Authorization": f"Bearer {admin_token}"}

        assert client.delete(draft_url, headers=headers).status_code == 404
        assert client.patch(draft_url, json={"title": "x"}, headers=headers).status_code == 404
        assert client.post(f"{draft_url}/approve", headers=headers).status_code == 404


@pytest.mark.integration
class TestApproveStoriesBulkEndpoint:
    """Test POST /v1/refinement/approve-stories endpoint."""

    def test_approve_stories_bulk_success(self, client: TestClient, admin_token: str, mock_story_response):
        with patch(
            "src.app.features.refinement.application.use_cases.approve_stories_bulk.ApproveStoriesBulkUseCase.execute",
            new=AsyncMock(return_value=[mock_story_response, mock_story_response]),
        ):
            response = client.post(
                "/v1/refinement/approve-stories",
                json={"stories": [APPROVE_BODY, APPROVE_BODY]},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["approvedCount"] == 2
        assert data["stories"][0] == {"id": "550e8400-e29b-41d4-a716-446655440100", "title": "Test Story"}

    def test_approve_stories_bulk_rejects_empty_list(self, client: TestClient, admin_token: str):
        response = client.post(
            "/v1/refinement/approve-stories",
            json={"stories": []},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_approve_stories_bulk_unauthorized_without_token(self, client: TestClient):
        response = client.post("/v1/refinement/approve-stories", json={"stories": [APPROVE_BODY]})

        assert response.status_code == 401


@pytest.mark.integration
class TestRefinementFailureHandling:
    """Test that provider failures preserve the Admin's raw notes (FR-002-04)."""

    def test_provider_failure_returns_502_with_preserved_notes(self, client: TestClient, admin_token: str):
        """Test that a provider failure echoes the raw notes back for retry."""
        raw_notes = "Client wants login, project tracking, and export to markdown."

        with patch(
            "src.app.features.refinement.application.use_cases.generate_stories_from_notes"
            ".GenerateStoriesFromNotesUseCase.execute",
            new=AsyncMock(
                side_effect=RefinementFailedError(
                    failure_class=RefinementFailureClass.TIMEOUT,
                    raw_notes=raw_notes,
                    provider="gemini",
                )
            ),
        ):
            response = client.post(
                "/v1/refinement/generate-stories",
                json={
                    "projectId": "550e8400-e29b-41d4-a716-446655440001",
                    "rawNotes": raw_notes,
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 502
        data = response.json()
        assert data["rawNotes"] == raw_notes
        assert data["failureClass"] == "timeout"
        assert data["provider"] == "gemini"
        assert "retry" in data["detail"].lower()

    def test_over_length_notes_are_rejected_with_the_limit(self, client: TestClient, admin_token: str):
        """Test that notes above the 5000-character cap are rejected before any AI call."""
        response = client.post(
            "/v1/refinement/generate-stories",
            json={
                "projectId": "550e8400-e29b-41d4-a716-446655440001",
                "rawNotes": "a" * 5001,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422
        assert "5000" in response.json()["detail"]
