"""Integration tests for project endpoints."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config.app_config import AppConfig
from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
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
def mock_project_entity():
    """Create a mock project entity."""
    entity_id = EntityId.from_string("550e8400-e29b-41d4-a716-446655440100")
    creator_id = EntityId.from_string("550e8400-e29b-41d4-a716-446655440001")
    client_id = EntityId.from_string("550e8400-e29b-41d4-a716-446655440003")
    return ProjectEntity(
        id=entity_id,
        name="Test Project",
        code="TEST",
        description="Test description",
        created_by=creator_id,
        client_id=client_id,
        status=ProjectStatus.ACTIVE,
        priority=ProjectPriority.MEDIUM,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 12, 31),
        created_at=datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def mock_project_response(mock_project_entity):
    """Create a mock project response DTO."""
    return ProjectResponse(
        id=str(mock_project_entity.id.value),
        name=mock_project_entity.name,
        code=mock_project_entity.code,
        description=mock_project_entity.description,
        created_by=str(mock_project_entity.created_by.value),
        client_id=str(mock_project_entity.client_id.value),
        client_name="Test Client",
        status=mock_project_entity.status.value,
        priority=mock_project_entity.priority.value,
        phase=mock_project_entity.phase.value,
        start_date=mock_project_entity.start_date,
        end_date=mock_project_entity.end_date,
        created_at=mock_project_entity.created_at.isoformat(),
        updated_at=mock_project_entity.updated_at.isoformat(),
    )


class TestCreateProjectEndpoint:
    """Test POST /v1/projects endpoint."""

    def test_create_project_success(self, client: TestClient, admin_token: str, mock_project_response):
        """Test creating project with valid data returns 201."""
        with patch(
            "src.app.features.projects.application.use_cases.create_project.CreateProjectUseCase.execute",
            new=AsyncMock(return_value=mock_project_response),
        ):
            response = client.post(
                "/v1/projects",
                json={
                    "name": "Test Project",
                    "code": "TEST",
                    "clientId": "550e8400-e29b-41d4-a716-446655440003",
                    "phase": "discovery",
                    "description": "Test description",
                    "startDate": "2026-05-01",
                    "endDate": "2026-12-31",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "Test description"
        assert data["status"] == "active"
        assert "id" in data

    def test_create_project_unauthorized_without_token(self, client: TestClient):
        """Test creating project without token returns 401."""
        response = client.post(
            "/v1/projects",
            json={"name": "Test Project"},
        )

        assert response.status_code == 401

    def test_create_project_conflict_at_active_limit(self, client: TestClient, admin_token: str, mock_project_response):
        """Test creating project at active-project limit returns 409."""
        from src.app.features.projects.domain.exceptions.project_exceptions import ActiveProjectLimitExceededError

        with patch(
            "src.app.features.projects.application.use_cases.create_project.CreateProjectUseCase.execute",
            new=AsyncMock(side_effect=ActiveProjectLimitExceededError(3)),
        ):
            response = client.post(
                "/v1/projects",
                json={
                    "name": "Test Project",
                    "code": "TEST",
                    "clientId": "550e8400-e29b-41d4-a716-446655440003",
                    "phase": "discovery",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 409
        assert "limit" in response.json()["detail"]

    def test_create_project_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test creating project as viewer returns 403."""
        response = client.post(
            "/v1/projects",
            json={"name": "Test Project"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


class TestListProjectsEndpoint:
    """Test GET /v1/projects endpoint."""

    def test_list_projects_returns_array(self, client: TestClient, admin_token: str, mock_project_response):
        """Test listing projects returns paginated response."""
        from src.app.shared.application.dtos.pagination_dto import PaginatedResponse

        paginated_response = PaginatedResponse(total=1, page=1, per_page=20, items=[mock_project_response])

        with patch(
            "src.app.features.projects.application.use_cases.list_projects.ListProjectsUseCase.execute",
            new=AsyncMock(return_value=paginated_response),
        ):
            response = client.get(
                "/v1/projects",
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
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["per_page"] == 20

    def test_list_projects_unauthorized_without_token(self, client: TestClient):
        """Test listing projects without token returns 401."""
        response = client.get("/v1/projects")

        assert response.status_code == 401

    def test_list_projects_accepts_filter_parameters(self, client: TestClient, admin_token: str, mock_project_response):
        """Test listing projects forwards filter query parameters."""
        from src.app.shared.application.dtos.pagination_dto import PaginatedResponse

        paginated_response = PaginatedResponse(total=1, page=1, per_page=20, items=[mock_project_response])

        with patch(
            "src.app.features.projects.application.use_cases.list_projects.ListProjectsUseCase.execute",
            new=AsyncMock(return_value=paginated_response),
        ) as mock_execute:
            response = client.get(
                "/v1/projects",
                params={
                    "status": "active",
                    "clientId": "550e8400-e29b-41d4-a716-446655440003",
                    "createdFrom": "2026-01-01T00:00:00Z",
                    "createdTo": "2026-06-30T23:59:59Z",
                    "search": "payroll",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        _, kwargs = mock_execute.call_args
        assert kwargs["status"] == "active"
        assert kwargs["client_id"] == "550e8400-e29b-41d4-a716-446655440003"
        assert kwargs["created_from"] is not None
        assert kwargs["created_to"] is not None
        assert kwargs["search"] == "payroll"


class TestGetProjectByIdEndpoint:
    """Test GET /v1/projects/{project_id} endpoint."""

    def test_get_project_by_id_success(self, client: TestClient, admin_token: str, mock_project_response):
        """Test getting project by ID returns project data."""
        with patch(
            "src.app.features.projects.application.use_cases.get_project_by_id.GetProjectByIdUseCase.execute",
            new=AsyncMock(return_value=mock_project_response),
        ):
            response = client.get(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440100",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_project_response.id)
        assert data["name"] == "Test Project"

    def test_get_project_by_id_not_found(self, client: TestClient, admin_token: str):
        """Test getting non-existent project returns 404."""
        with patch(
            "src.app.features.projects.application.use_cases.get_project_by_id.GetProjectByIdUseCase.execute",
            new=AsyncMock(return_value=None),
        ):
            response = client.get(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404


class TestUpdateProjectEndpoint:
    """Test PATCH /v1/projects/{project_id} endpoint."""

    def test_update_project_name(self, client: TestClient, admin_token: str, mock_project_response):
        """Test updating project name."""
        updated_response = ProjectResponse(
            id=mock_project_response.id,
            name="Updated Name",
            code=mock_project_response.code,
            description=mock_project_response.description,
            created_by=mock_project_response.created_by,
            client_id=mock_project_response.client_id,
            client_name=mock_project_response.client_name,
            status=mock_project_response.status,
            priority=mock_project_response.priority,
            phase=mock_project_response.phase,
            start_date=mock_project_response.start_date,
            end_date=mock_project_response.end_date,
            created_at=mock_project_response.created_at,
            updated_at=datetime.now(tz=UTC).isoformat(),
        )
        with patch(
            "src.app.features.projects.application.use_cases.update_project.UpdateProjectUseCase.execute",
            new=AsyncMock(return_value=updated_response),
        ):
            response = client.patch(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440100",
                json={"name": "Updated Name"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_project_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test updating project as viewer returns 403."""
        response = client.patch(
            "/v1/projects/550e8400-e29b-41d4-a716-446655440001",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


class TestDeleteProjectEndpoint:
    """Test DELETE /v1/projects/{project_id} endpoint."""

    def test_delete_project_success(self, client: TestClient, admin_token: str):
        """Test deleting project returns 204."""
        with patch(
            "src.app.features.projects.application.use_cases.delete_project.DeleteProjectUseCase.execute",
            new=AsyncMock(return_value=None),
        ):
            response = client.delete(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440100",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 204

    def test_delete_project_not_found(self, client: TestClient, admin_token: str):
        """Test deleting non-existent project returns 404."""
        from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError

        with patch(
            "src.app.features.projects.application.use_cases.delete_project.DeleteProjectUseCase.execute",
            new=AsyncMock(side_effect=ProjectNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.delete(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_delete_project_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test deleting project as viewer returns 403."""
        response = client.delete(
            "/v1/projects/550e8400-e29b-41d4-a716-446655440001",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


class TestArchiveProjectEndpoint:
    """Test POST /v1/projects/{project_id}/archive endpoint."""

    def test_archive_project_success(self, client: TestClient, admin_token: str, mock_project_response):
        """Test archiving project returns 200 with archived status."""
        archived_response = ProjectResponse(
            id=mock_project_response.id,
            name=mock_project_response.name,
            code=mock_project_response.code,
            description=mock_project_response.description,
            created_by=mock_project_response.created_by,
            client_id=mock_project_response.client_id,
            client_name=mock_project_response.client_name,
            status="archived",
            priority=mock_project_response.priority,
            phase=mock_project_response.phase,
            start_date=mock_project_response.start_date,
            end_date=mock_project_response.end_date,
            created_at=mock_project_response.created_at,
            updated_at=datetime.now(tz=UTC).isoformat(),
        )
        with patch(
            "src.app.features.projects.application.use_cases.archive_project.ArchiveProjectUseCase.execute",
            new=AsyncMock(return_value=archived_response),
        ):
            response = client.post(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440100/archive",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "archived"

    def test_archive_project_not_found(self, client: TestClient, admin_token: str):
        """Test archiving non-existent project returns 404."""
        from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError

        with patch(
            "src.app.features.projects.application.use_cases.archive_project.ArchiveProjectUseCase.execute",
            new=AsyncMock(side_effect=ProjectNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.post(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440999/archive",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_archive_project_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test archiving project as viewer returns 403."""
        response = client.post(
            "/v1/projects/550e8400-e29b-41d4-a716-446655440100/archive",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403


class TestReactivateProjectEndpoint:
    """Test POST /v1/projects/{project_id}/reactivate endpoint."""

    def test_reactivate_project_success(self, client: TestClient, admin_token: str, mock_project_response):
        """Test reactivating project returns 200 with active status."""
        reactivated_response = ProjectResponse(
            id=mock_project_response.id,
            name=mock_project_response.name,
            code=mock_project_response.code,
            description=mock_project_response.description,
            created_by=mock_project_response.created_by,
            client_id=mock_project_response.client_id,
            client_name=mock_project_response.client_name,
            status="active",
            priority=mock_project_response.priority,
            phase=mock_project_response.phase,
            start_date=mock_project_response.start_date,
            end_date=mock_project_response.end_date,
            created_at=mock_project_response.created_at,
            updated_at=datetime.now(tz=UTC).isoformat(),
        )
        with patch(
            "src.app.features.projects.application.use_cases.reactivate_project.ReactivateProjectUseCase.execute",
            new=AsyncMock(return_value=reactivated_response),
        ):
            response = client.post(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440100/reactivate",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_reactivate_project_not_found(self, client: TestClient, admin_token: str):
        """Test reactivating non-existent project returns 404."""
        from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError

        with patch(
            "src.app.features.projects.application.use_cases.reactivate_project.ReactivateProjectUseCase.execute",
            new=AsyncMock(side_effect=ProjectNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.post(
                "/v1/projects/550e8400-e29b-41d4-a716-446655440999/reactivate",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_reactivate_project_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test reactivating project as viewer returns 403."""
        response = client.post(
            "/v1/projects/550e8400-e29b-41d4-a716-446655440100/reactivate",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403
