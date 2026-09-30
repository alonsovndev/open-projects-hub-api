"""Integration tests for refinement endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config.app_config import AppConfig
from src.app.features.refinement.application.dtos.refinement_dto import (
    GeneratedStoryResponse,
    GenerateStoriesResponse,
    ListStoryDraftsResponse,
)
from src.app.features.refinement.application.mappers.story_draft_mapper import to_story_draft_response
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.exceptions.refinement_exceptions import (
    RefinementFailedError,
    StoryDraftNotFoundError,
)
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.features.refinement.domain.value_objects.refinement_failure_class import RefinementFailureClass
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.shared.domain.value_objects.entity_id import EntityId
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
def viewer_token(app_jwt_handler):
    """Generate viewer JWT token for tests."""
    return app_jwt_handler.create_access_token(
        user_id="550e8400-e29b-41d4-a716-446655440002",
        email="viewer@example.com",
        role="viewer",
        workspace_id="550e8400-e29b-41d4-a716-4466554400ff",
    )


@pytest.fixture
def mock_draft_entity():
    """Create a mock draft entity."""
    return StoryDraftEntity(
        id=EntityId.from_string("550e8400-e29b-41d4-a716-446655440100"),
        title="Test Draft",
        description="Test description",
        acceptance_criteria=["Criterion 1"],
        project_id=EntityId.from_string("550e8400-e29b-41d4-a716-446655440001"),
        created_by=EntityId.from_string("550e8400-e29b-41d4-a716-446655440001"),
        status=DraftStatus.DRAFT,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
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
class TestUpdateDraftEndpoint:
    """Test PATCH /v1/refinement/drafts/{draft_id} endpoint."""

    def test_update_draft_success(self, client: TestClient, admin_token: str, mock_draft_entity):
        """Test updating draft with valid data returns 200."""
        with patch(
            "src.app.features.refinement.application.use_cases.update_story_draft.UpdateStoryDraftUseCase.execute",
            new=AsyncMock(return_value=mock_draft_entity),
        ):
            response = client.patch(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
                json={
                    "title": "Updated Title",
                    "description": "Updated description",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440100"

    def test_update_draft_not_found(self, client: TestClient, admin_token: str):
        """Test updating non-existent draft returns 404."""
        with patch(
            "src.app.features.refinement.application.use_cases.update_story_draft.UpdateStoryDraftUseCase.execute",
            new=AsyncMock(side_effect=StoryDraftNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.patch(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440999",
                json={"title": "Updated Title"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_update_draft_unauthorized_without_token(self, client: TestClient):
        """Test updating draft without token returns 401."""
        response = client.patch(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 401

    def test_update_draft_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test updating draft with viewer role returns 403."""
        response = client.patch(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403

    def test_update_draft_validation_error_empty_title(self, client: TestClient, admin_token: str):
        """Test updating draft with empty title returns 422."""
        response = client.patch(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
            json={"title": ""},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_update_draft_camel_case_serialization(self, client: TestClient, admin_token: str, mock_draft_entity):
        """Test that request accepts camelCase JSON."""
        with patch(
            "src.app.features.refinement.application.use_cases.update_story_draft.UpdateStoryDraftUseCase.execute",
            new=AsyncMock(return_value=mock_draft_entity),
        ):
            response = client.patch(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
                json={
                    "title": "Updated Title",
                    "acceptanceCriteria": ["New criterion"],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200


@pytest.mark.integration
class TestGenerateStoriesEndpoint:
    """Test POST /v1/refinement/generate-stories endpoint."""

    def test_generate_stories_success(self, client: TestClient, admin_token: str):
        """Test generating stories returns 200."""
        mock_response = GenerateStoriesResponse(
            stories=[
                GeneratedStoryResponse(
                    id="550e8400-e29b-41d4-a716-446655440100",
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

    def test_generate_stories_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test generating stories with viewer role returns 403."""
        response = client.post(
            "/v1/refinement/generate-stories",
            json={
                "projectId": "550e8400-e29b-41d4-a716-446655440001",
                "rawNotes": "Some raw notes that are long enough",
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403

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
                    id="550e8400-e29b-41d4-a716-446655440100",
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


@pytest.mark.integration
class TestApproveDraftEndpoint:
    """Test POST /v1/refinement/drafts/{draft_id}/approve endpoint."""

    def test_approve_draft_success(self, client: TestClient, admin_token: str, mock_story_response):
        """Test approving draft returns 200 with story."""
        with patch(
            "src.app.features.refinement.application.use_cases.approve_draft.ApproveDraftUseCase.execute",
            new=AsyncMock(return_value=mock_story_response),
        ):
            response = client.post(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100/approve",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440100"
        assert data["title"] == "Test Story"

    def test_approve_draft_not_found(self, client: TestClient, admin_token: str):
        """Test approving non-existent draft returns 404."""
        with patch(
            "src.app.features.refinement.application.use_cases.approve_draft.ApproveDraftUseCase.execute",
            new=AsyncMock(side_effect=StoryDraftNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.post(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440999/approve",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_approve_draft_unauthorized_without_token(self, client: TestClient):
        """Test approving draft without token returns 401."""
        response = client.post(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100/approve",
        )

        assert response.status_code == 401

    def test_approve_draft_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test approving draft with viewer role returns 403."""
        response = client.post(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100/approve",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestApproveDraftsBulkEndpoint:
    """Test POST /v1/refinement/approve-drafts endpoint."""

    def test_approve_drafts_bulk_success(self, client: TestClient, admin_token: str):
        """Test bulk approving drafts returns 200."""
        mock_story_1 = StoryResponse(
            id="550e8400-e29b-41d4-a716-446655440100",
            title="Story 1",
            description="Description 1",
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
        mock_story_2 = StoryResponse(
            id="550e8400-e29b-41d4-a716-446655440101",
            title="Story 2",
            description="Description 2",
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

        with patch(
            "src.app.features.refinement.application.use_cases.approve_drafts_bulk.ApproveDraftsBulkUseCase.execute",
            new=AsyncMock(return_value=[mock_story_1, mock_story_2]),
        ):
            response = client.post(
                "/v1/refinement/approve-drafts",
                json={
                    "draftIds": [
                        "550e8400-e29b-41d4-a716-446655440100",
                        "550e8400-e29b-41d4-a716-446655440101",
                    ],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["approvedCount"] == 2
        assert len(data["stories"]) == 2
        assert data["stories"][0]["title"] == "Story 1"

    def test_approve_drafts_bulk_no_drafts_found(self, client: TestClient, admin_token: str):
        """Test bulk approving with no found drafts returns 400."""
        with patch(
            "src.app.features.refinement.application.use_cases.approve_drafts_bulk.ApproveDraftsBulkUseCase.execute",
            new=AsyncMock(return_value=[]),
        ):
            response = client.post(
                "/v1/refinement/approve-drafts",
                json={
                    "draftIds": ["550e8400-e29b-41d4-a716-446655440999"],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 400

    def test_approve_drafts_bulk_unauthorized_without_token(self, client: TestClient):
        """Test bulk approving drafts without token returns 401."""
        response = client.post(
            "/v1/refinement/approve-drafts",
            json={
                "draftIds": ["550e8400-e29b-41d4-a716-446655440100"],
            },
        )

        assert response.status_code == 401

    def test_approve_drafts_bulk_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test bulk approving drafts with viewer role returns 403."""
        response = client.post(
            "/v1/refinement/approve-drafts",
            json={
                "draftIds": ["550e8400-e29b-41d4-a716-446655440100"],
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403

    def test_approve_drafts_bulk_validation_error_empty_ids(self, client: TestClient, admin_token: str):
        """Test bulk approving with empty draftIds returns 422."""
        response = client.post(
            "/v1/refinement/approve-drafts",
            json={
                "draftIds": [],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_approve_drafts_bulk_camel_case_serialization(self, client: TestClient, admin_token: str):
        """Test that request and response use camelCase."""
        mock_story = StoryResponse(
            id="550e8400-e29b-41d4-a716-446655440100",
            title="Story",
            description="Description",
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

        with patch(
            "src.app.features.refinement.application.use_cases.approve_drafts_bulk.ApproveDraftsBulkUseCase.execute",
            new=AsyncMock(return_value=[mock_story]),
        ):
            response = client.post(
                "/v1/refinement/approve-drafts",
                json={
                    "draftIds": ["550e8400-e29b-41d4-a716-446655440100"],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "approvedCount" in data
        assert "stories" in data


@pytest.mark.integration
class TestListDraftsEndpoint:
    """Test GET /v1/refinement/projects/{project_id}/drafts endpoint."""

    def test_list_drafts_success(self, client: TestClient, admin_token: str, mock_draft_entity):
        """Test listing drafts for a project returns 200 with camelCase payload."""
        mock_response = ListStoryDraftsResponse(
            drafts=[to_story_draft_response(mock_draft_entity)],
            total=1,
        )

        with patch(
            "src.app.features.refinement.application.use_cases.list_story_drafts.ListStoryDraftsUseCase.execute",
            new=AsyncMock(return_value=mock_response),
        ):
            response = client.get(
                "/v1/refinement/projects/550e8400-e29b-41d4-a716-446655440001/drafts?status=draft",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["drafts"][0]["acceptanceCriteria"] == ["Criterion 1"]
        assert data["drafts"][0]["status"] == "draft"

    def test_list_drafts_rejects_unknown_status(self, client: TestClient, admin_token: str):
        """Test that an unsupported status filter returns 422."""
        response = client.get(
            "/v1/refinement/projects/550e8400-e29b-41d4-a716-446655440001/drafts?status=approved",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_list_drafts_unauthorized_without_token(self, client: TestClient):
        """Test listing drafts without token returns 401."""
        response = client.get("/v1/refinement/projects/550e8400-e29b-41d4-a716-446655440001/drafts")

        assert response.status_code == 401

    def test_list_drafts_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test that a Viewer can never read unapproved drafts."""
        response = client.get(
            "/v1/refinement/projects/550e8400-e29b-41d4-a716-446655440001/drafts",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestDeleteDraftEndpoint:
    """Test DELETE /v1/refinement/drafts/{draft_id} endpoint."""

    def test_delete_draft_success(self, client: TestClient, admin_token: str):
        """Test discarding a draft returns 204."""
        with patch(
            "src.app.features.refinement.application.use_cases.delete_story_draft.DeleteStoryDraftUseCase.execute",
            new=AsyncMock(return_value=None),
        ):
            response = client.delete(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 204

    def test_delete_draft_not_found(self, client: TestClient, admin_token: str):
        """Test discarding an unknown draft returns 404."""
        with patch(
            "src.app.features.refinement.application.use_cases.delete_story_draft.DeleteStoryDraftUseCase.execute",
            new=AsyncMock(side_effect=StoryDraftNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.delete(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_delete_draft_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test discarding a draft with viewer role returns 403."""
        response = client.delete(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


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
