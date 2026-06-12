"""Integration tests for story endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.app import fastapi_app
from src.app.config.app_config import AppConfig
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler


@pytest.mark.integration
@pytest.fixture
def client():
    """Create test client."""
    return TestClient(fastapi_app)


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
def mock_story_response():
    """Create a mock story response DTO."""
    return StoryResponse(
        id="550e8400-e29b-41d4-a716-446655440100",
        title="Test Story",
        description="Test description",
        project_id="550e8400-e29b-41d4-a716-446655440001",
        created_by="550e8400-e29b-41d4-a716-446655440001",
        assigned_to="550e8400-e29b-41d4-a716-446655440002",
        status="todo",
        priority="medium",
        points=5,
        created_at="2026-05-09T12:00:00",
        updated_at="2026-05-09T12:00:00",
    )


class TestCreateStoryEndpoint:
    """Test POST /v1/stories endpoint."""

    def test_create_story_success(self, client: TestClient, admin_token: str, mock_story_response):
        """Test creating story with valid data returns 201."""
        with patch(
            "src.app.features.stories.application.use_cases.create_story.CreateStoryUseCase.execute",
            new=AsyncMock(return_value=mock_story_response),
        ):
            response = client.post(
                "/v1/stories",
                json={
                    "title": "Test Story",
                    "description": "Test description",
                    "project_id": "550e8400-e29b-41d4-a716-446655440001",
                    "priority": "medium",
                    "points": 5,
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Story"
        assert data["description"] == "Test description"
        assert data["status"] == "todo"
        assert "id" in data

    def test_create_story_unauthorized_without_token(self, client: TestClient):
        """Test creating story without token returns 403."""
        response = client.post(
            "/v1/stories",
            json={"title": "Test Story", "project_id": "550e8400-e29b-41d4-a716-446655440001"},
        )

        assert response.status_code == 403


class TestListStoriesEndpoint:
    """Test GET /v1/stories endpoint."""

    def test_list_stories_returns_array(self, client: TestClient, admin_token: str, mock_story_response):
        """Test listing stories returns paginated response."""
        from src.app.shared.application.dtos.pagination_dto import PaginatedResponse

        paginated_response = PaginatedResponse(total=1, page=1, per_page=20, items=[mock_story_response])

        with patch(
            "src.app.features.stories.application.use_cases.list_stories.ListStoriesUseCase.execute",
            new=AsyncMock(return_value=paginated_response),
        ):
            response = client.get(
                "/v1/stories",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_stories_with_filters(self, client: TestClient, admin_token: str, mock_story_response):
        """Test listing stories with status filter."""
        from src.app.shared.application.dtos.pagination_dto import PaginatedResponse

        paginated_response = PaginatedResponse(total=1, page=1, per_page=20, items=[mock_story_response])

        with patch(
            "src.app.features.stories.application.use_cases.list_stories.ListStoriesUseCase.execute",
            new=AsyncMock(return_value=paginated_response),
        ):
            response = client.get(
                "/v1/stories?status=todo&priority=high",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data

    def test_list_stories_unauthorized_without_token(self, client: TestClient):
        """Test listing stories without token returns 403."""
        response = client.get("/v1/stories")

        assert response.status_code == 403


class TestGetStoryByIdEndpoint:
    """Test GET /v1/stories/{story_id} endpoint."""

    def test_get_story_by_id_success(self, client: TestClient, admin_token: str, mock_story_response):
        """Test getting story by ID returns story data."""
        with patch(
            "src.app.features.stories.application.use_cases.get_story_by_id.GetStoryByIdUseCase.execute",
            new=AsyncMock(return_value=mock_story_response),
        ):
            response = client.get(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440100",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "550e8400-e29b-41d4-a716-446655440100"
        assert data["title"] == "Test Story"

    def test_get_story_by_id_not_found(self, client: TestClient, admin_token: str):
        """Test getting non-existent story returns 404."""
        with patch(
            "src.app.features.stories.application.use_cases.get_story_by_id.GetStoryByIdUseCase.execute",
            new=AsyncMock(side_effect=StoryNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.get(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404


class TestUpdateStoryEndpoint:
    """Test PATCH /v1/stories/{story_id} endpoint."""

    def test_update_story_title(self, client: TestClient, admin_token: str, mock_story_response):
        """Test updating story title."""
        updated_response = StoryResponse(
            id=mock_story_response.id,
            title="Updated Title",
            description=mock_story_response.description,
            project_id=mock_story_response.project_id,
            created_by=mock_story_response.created_by,
            assigned_to=mock_story_response.assigned_to,
            status=mock_story_response.status,
            priority=mock_story_response.priority,
            points=mock_story_response.points,
            created_at=mock_story_response.created_at,
            updated_at=datetime.now(tz=UTC).isoformat(),
        )
        with patch(
            "src.app.features.stories.application.use_cases.update_story.UpdateStoryUseCase.execute",
            new=AsyncMock(return_value=updated_response),
        ):
            response = client.patch(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440100",
                json={"title": "Updated Title"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_story_not_found(self, client: TestClient, admin_token: str):
        """Test updating non-existent story returns 404."""
        with patch(
            "src.app.features.stories.application.use_cases.update_story.UpdateStoryUseCase.execute",
            new=AsyncMock(side_effect=StoryNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.patch(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440999",
                json={"title": "Updated"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404


class TestDeleteStoryEndpoint:
    """Test DELETE /v1/stories/{story_id} endpoint."""

    def test_delete_story_success(self, client: TestClient, admin_token: str):
        """Test deleting story returns 204."""
        with patch(
            "src.app.features.stories.application.use_cases.delete_story.DeleteStoryUseCase.execute",
            new=AsyncMock(return_value=True),
        ):
            response = client.delete(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440100",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 204

    def test_delete_story_not_found(self, client: TestClient, admin_token: str):
        """Test deleting non-existent story returns 404."""
        with patch(
            "src.app.features.stories.application.use_cases.delete_story.DeleteStoryUseCase.execute",
            new=AsyncMock(side_effect=StoryNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.delete(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404


class TestGetStoriesByProjectEndpoint:
    """Test GET /v1/stories/by-project/{project_id} endpoint."""

    def test_get_stories_by_project_success(self, client: TestClient, admin_token: str, mock_story_response):
        """Test getting stories by project returns paginated response."""
        from src.app.shared.application.dtos.pagination_dto import PaginatedResponse

        paginated_response = PaginatedResponse(total=1, page=1, per_page=20, items=[mock_story_response])

        with patch(
            "src.app.features.stories.application.use_cases.get_stories_by_project.GetStoriesByProjectUseCase.execute",
            new=AsyncMock(return_value=paginated_response),
        ):
            response = client.get(
                "/v1/stories/by-project/550e8400-e29b-41d4-a716-446655440001",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)


class TestAssignStoryEndpoint:
    """Test POST /v1/stories/{story_id}/assign endpoint."""

    def test_assign_story_success(self, client: TestClient, admin_token: str, mock_story_response):
        """Test assigning story to user."""
        assigned_response = StoryResponse(
            id=mock_story_response.id,
            title=mock_story_response.title,
            description=mock_story_response.description,
            project_id=mock_story_response.project_id,
            created_by=mock_story_response.created_by,
            assigned_to="550e8400-e29b-41d4-a716-446655440003",
            status=mock_story_response.status,
            priority=mock_story_response.priority,
            points=mock_story_response.points,
            created_at=mock_story_response.created_at,
            updated_at=datetime.now(tz=UTC).isoformat(),
        )
        with patch(
            "src.app.features.stories.application.use_cases.assign_story.AssignStoryUseCase.execute",
            new=AsyncMock(return_value=assigned_response),
        ):
            response = client.post(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440100/assign",
                json={"user_id": "550e8400-e29b-41d4-a716-446655440003"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["assignedTo"] == "550e8400-e29b-41d4-a716-446655440003"

    def test_assign_story_not_found(self, client: TestClient, admin_token: str):
        """Test assigning non-existent story returns 404."""
        with patch(
            "src.app.features.stories.application.use_cases.assign_story.AssignStoryUseCase.execute",
            new=AsyncMock(side_effect=StoryNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.post(
                "/v1/stories/550e8400-e29b-41d4-a716-446655440999/assign",
                json={"user_id": "550e8400-e29b-41d4-a716-446655440003"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404
