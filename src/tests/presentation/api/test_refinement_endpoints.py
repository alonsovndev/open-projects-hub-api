"""Integration tests for refinement endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.app import fastApiApp
from src.app.config.app_config import AppConfig
from src.app.features.refinement.application.dtos.refinement_dto import GeneratedStoryResponse, GenerateStoriesResponse
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


@pytest.mark.integration
@pytest.fixture
def client():
    """Create test client."""
    return TestClient(fastApiApp)


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
def mock_draft_entity():
    """Create a mock draft entity."""
    return StoryDraftEntity(
        id=EntityId.from_string("550e8400-e29b-41d4-a716-446655440100"),
        title="Test Draft",
        description="Test description",
        acceptance_criteria=["Criterion 1"],
        project_id=EntityId.from_string("550e8400-e29b-41d4-a716-446655440001"),
        created_by=EntityId.from_string("550e8400-e29b-41d4-a716-446655440001"),
        status=RefinementStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_story_response():
    """Create a mock story response DTO."""
    return StoryResponse(
        id="550e8400-e29b-41d4-a716-446655440100",
        title="Test Story",
        description="Test description",
        project_id="550e8400-e29b-41d4-a716-446655440001",
        created_by="550e8400-e29b-41d4-a716-446655440001",
        assigned_to=None,
        status="todo",
        priority="medium",
        points=None,
        created_at="2026-05-21T12:00:00",
        updated_at="2026-05-21T12:00:00",
    )


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
            new=AsyncMock(return_value=None),
        ):
            response = client.patch(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440999",
                json={"title": "Updated Title"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_update_draft_unauthorized_without_token(self, client: TestClient):
        """Test updating draft without token returns 403."""
        response = client.patch(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 403

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

    def test_update_draft_camelCase_serialization(self, client: TestClient, admin_token: str, mock_draft_entity):
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
                    confidence=0.9,
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
        assert data["stories"][0]["confidence"] == 0.9
        assert data["rawNotes"] == "Some raw notes"

    def test_generate_stories_unauthorized_without_token(self, client: TestClient):
        """Test generating stories without token returns 403."""
        response = client.post(
            "/v1/refinement/generate-stories",
            json={
                "projectId": "550e8400-e29b-41d4-a716-446655440001",
                "rawNotes": "Some raw notes that are long enough",
            },
        )

        assert response.status_code == 403

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

    def test_generate_stories_camelCase_serialization(self, client: TestClient, admin_token: str):
        """Test that request and response use camelCase."""
        mock_response = GenerateStoriesResponse(
            stories=[
                GeneratedStoryResponse(
                    id="550e8400-e29b-41d4-a716-446655440100",
                    title="Story",
                    description="Desc",
                    acceptance_criteria=["Crit"],
                    confidence=0.8,
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
            new=AsyncMock(return_value=None),
        ):
            response = client.post(
                "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440999/approve",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_approve_draft_unauthorized_without_token(self, client: TestClient):
        """Test approving draft without token returns 403."""
        response = client.post(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100/approve",
        )

        assert response.status_code == 403

    def test_approve_draft_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test approving draft with viewer role returns 403."""
        response = client.post(
            "/v1/refinement/drafts/550e8400-e29b-41d4-a716-446655440100/approve",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


class TestApproveDraftsBulkEndpoint:
    """Test POST /v1/refinement/approve-drafts endpoint."""

    def test_approve_drafts_bulk_success(self, client: TestClient, admin_token: str):
        """Test bulk approving drafts returns 200."""
        mock_story_1 = StoryResponse(
            id="550e8400-e29b-41d4-a716-446655440100",
            title="Story 1",
            description="Description 1",
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
        """Test bulk approving drafts without token returns 403."""
        response = client.post(
            "/v1/refinement/approve-drafts",
            json={
                "draftIds": ["550e8400-e29b-41d4-a716-446655440100"],
            },
        )

        assert response.status_code == 403

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

    def test_approve_drafts_bulk_camelCase_serialization(self, client: TestClient, admin_token: str):
        """Test that request and response use camelCase."""
        mock_story = StoryResponse(
            id="550e8400-e29b-41d4-a716-446655440100",
            title="Story",
            description="Description",
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
