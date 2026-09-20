"""Integration tests for client endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config.app_config import AppConfig
from src.app.features.clients.application.dtos.client_dto import ClientResponse, PaginatedClientsResponse
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.domain.exceptions.client_exceptions import (
    ClientHasActiveProjectsError,
    ClientNotFoundError,
)
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
def mock_client_entity():
    """Create a mock client entity."""
    entity_id = EntityId.from_string("550e8400-e29b-41d4-a716-446655440200")
    return ClientEntity(
        id=entity_id,
        name="Test Client",
        company="Test Company",
        created_at=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def mock_client_response(mock_client_entity):
    """Create a mock client response DTO."""
    return ClientResponse(
        id=str(mock_client_entity.id.value),
        name=mock_client_entity.name,
        email=None,
        phone=None,
        company=mock_client_entity.company,
        address=None,
        notes=None,
        created_at=mock_client_entity.created_at.isoformat(),
        updated_at=mock_client_entity.updated_at.isoformat(),
    )


class TestCreateClientEndpoint:
    """Test POST /v1/clients endpoint."""

    def test_create_client_success(self, client: TestClient, admin_token: str, mock_client_response):
        """Test creating client with valid data returns 201."""
        with patch(
            "src.app.features.clients.application.use_cases.create_client.CreateClientUseCase.execute",
            new=AsyncMock(return_value=mock_client_response),
        ):
            response = client.post(
                "/v1/clients",
                json={
                    "name": "Test Client",
                    "company": "Test Company",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Client"
        assert data["company"] == "Test Company"
        assert "id" in data

    def test_create_client_unauthorized_without_token(self, client: TestClient):
        """Test creating client without token returns 401."""
        response = client.post(
            "/v1/clients",
            json={"name": "Test Client"},
        )

        assert response.status_code == 401

    def test_create_client_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test creating client as viewer returns 403."""
        response = client.post(
            "/v1/clients",
            json={"name": "Test Client"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403

    def test_create_client_validation_error(self, client: TestClient, admin_token: str):
        """Test creating client with empty name returns 422."""
        response = client.post(
            "/v1/clients",
            json={"name": ""},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422

    def test_create_client_camelcase_json(self, client: TestClient, admin_token: str, mock_client_response):
        """Test that request accepts camelCase JSON."""
        with patch(
            "src.app.features.clients.application.use_cases.create_client.CreateClientUseCase.execute",
            new=AsyncMock(return_value=mock_client_response),
        ):
            response = client.post(
                "/v1/clients",
                json={
                    "name": "Test Client",
                    "company": "Test Company",
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 201


class TestListClientsEndpoint:
    """Test GET /v1/clients endpoint."""

    def test_list_clients_returns_paginated_response(self, client: TestClient, admin_token: str, mock_client_response):
        """Test listing clients returns paginated response."""
        paginated_response = PaginatedClientsResponse(
            total=1,
            page=1,
            per_page=20,
            items=[mock_client_response],
        )

        with patch(
            "src.app.features.clients.application.use_cases.get_clients.GetClientsUseCase.execute",
            new=AsyncMock(return_value=paginated_response),
        ):
            response = client.get(
                "/v1/clients",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "total" in data
        assert "page" in data
        assert "perPage" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["perPage"] == 20

    def test_list_clients_unauthorized_without_token(self, client: TestClient):
        """Test listing clients without token returns 401."""
        response = client.get("/v1/clients")

        assert response.status_code == 401

    def test_list_clients_with_pagination_params(self, client: TestClient, admin_token: str, mock_client_response):
        """Test listing clients with pagination parameters."""
        paginated_response = PaginatedClientsResponse(
            total=5,
            page=2,
            per_page=2,
            items=[mock_client_response],
        )

        with patch(
            "src.app.features.clients.application.use_cases.get_clients.GetClientsUseCase.execute",
            new=AsyncMock(return_value=paginated_response),
        ):
            response = client.get(
                "/v1/clients?offset=2&limit=2",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["perPage"] == 2


class TestGetClientByIdEndpoint:
    """Test GET /v1/clients/{client_id} endpoint."""

    def test_get_client_by_id_success(self, client: TestClient, admin_token: str, mock_client_response):
        """Test getting client by ID returns client data."""
        with patch(
            "src.app.features.clients.application.use_cases.get_client_by_id.GetClientByIdUseCase.execute",
            new=AsyncMock(return_value=mock_client_response),
        ):
            response = client.get(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mock_client_response.id)
        assert data["name"] == "Test Client"

    def test_get_client_by_id_not_found(self, client: TestClient, admin_token: str):
        """Test getting non-existent client returns 404."""
        with patch(
            "src.app.features.clients.application.use_cases.get_client_by_id.GetClientByIdUseCase.execute",
            new=AsyncMock(side_effect=ClientNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.get(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_get_client_by_id_unauthorized(self, client: TestClient):
        """Test getting client without token returns 401."""
        response = client.get("/v1/clients/550e8400-e29b-41d4-a716-446655440200")

        assert response.status_code == 401


class TestUpdateClientEndpoint:
    """Test PUT /v1/clients/{client_id} endpoint."""

    def test_update_client_success(self, client: TestClient, admin_token: str, mock_client_response):
        """Test updating client returns updated data."""
        updated_response = ClientResponse(
            id=mock_client_response.id,
            name="Updated Name",
            email=mock_client_response.email,
            phone=mock_client_response.phone,
            company="Updated Company",
            address=mock_client_response.address,
            notes=mock_client_response.notes,
            created_at=mock_client_response.created_at,
            updated_at=datetime.now(tz=UTC).isoformat(),
        )

        with patch(
            "src.app.features.clients.application.use_cases.update_client.UpdateClientUseCase.execute",
            new=AsyncMock(return_value=updated_response),
        ):
            response = client.put(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
                json={"name": "Updated Name", "company": "Updated Company"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["company"] == "Updated Company"

    def test_update_client_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test updating client as viewer returns 403."""
        response = client.put(
            "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403

    def test_update_client_not_found(self, client: TestClient, admin_token: str):
        """Test updating non-existent client returns 404."""
        with patch(
            "src.app.features.clients.application.use_cases.update_client.UpdateClientUseCase.execute",
            new=AsyncMock(side_effect=ClientNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.put(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440999",
                json={"name": "Updated"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_update_client_validation_error(self, client: TestClient, admin_token: str):
        """Test updating client with empty name returns 422."""
        response = client.put(
            "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
            json={"name": ""},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422


class TestDeleteClientEndpoint:
    """Test DELETE /v1/clients/{client_id} endpoint."""

    def test_delete_client_success(self, client: TestClient, admin_token: str):
        """Test deleting client returns 204."""
        with patch(
            "src.app.features.clients.application.use_cases.delete_client.DeleteClientUseCase.execute",
            new=AsyncMock(return_value=True),
        ):
            response = client.delete(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 204

    def test_delete_client_forbidden_for_viewer(self, client: TestClient, viewer_token: str):
        """Test deleting client as viewer returns 403."""
        response = client.delete(
            "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )

        assert response.status_code == 403

    def test_delete_client_not_found(self, client: TestClient, admin_token: str):
        """Test deleting non-existent client returns 404."""
        with patch(
            "src.app.features.clients.application.use_cases.delete_client.DeleteClientUseCase.execute",
            new=AsyncMock(side_effect=ClientNotFoundError("550e8400-e29b-41d4-a716-446655440999")),
        ):
            response = client.delete(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 404

    def test_delete_client_conflict_when_active_projects_exist(self, client: TestClient, admin_token: str):
        """Test deleting a client with active projects returns 409."""
        with patch(
            "src.app.features.clients.application.use_cases.delete_client.DeleteClientUseCase.execute",
            new=AsyncMock(
                side_effect=ClientHasActiveProjectsError("550e8400-e29b-41d4-a716-446655440200"),
            ),
        ):
            response = client.delete(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 409
        assert "active projects" in response.json()["detail"]


class TestCamelCaseJsonSerialization:
    """Test camelCase JSON serialization."""

    def test_response_uses_camel_case(self, client: TestClient, admin_token: str, mock_client_response):
        """Test that response DTO uses camelCase field names."""
        with patch(
            "src.app.features.clients.application.use_cases.get_client_by_id.GetClientByIdUseCase.execute",
            new=AsyncMock(return_value=mock_client_response),
        ):
            response = client.get(
                "/v1/clients/550e8400-e29b-41d4-a716-446655440200",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "createdAt" in data
        assert "updatedAt" in data
