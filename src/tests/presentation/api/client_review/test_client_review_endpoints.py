"""Endpoint tests for the public Client Review route."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.features.backlog.application.dtos.backlog_dto import BacklogStoryResponse
from src.app.features.client_review.application.dtos.client_review_dto import ClientReviewResponse
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter


ACCESS_CODE = "PRJ-7K3M9XQ2"
URL = f"/v1/viewer/{ACCESS_CODE}"
USE_CASE = "src.app.features.client_review.application.use_cases.get_client_review.GetClientReviewUseCase.execute"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Rate limit counters are process-wide; clear them so tests do not exhaust each other's budget."""
    limiter._storage.storage.clear()
    yield
    limiter._storage.storage.clear()


@pytest.fixture
def client_review_response():
    return ClientReviewResponse(
        project_name="Acme Portal",
        phase="discovery",
        total=1,
        stories=[
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


class TestGetClientReviewEndpoint:
    def test_is_readable_without_a_token(self, client: TestClient, client_review_response):
        with patch(USE_CASE, new=AsyncMock(return_value=client_review_response)):
            response = client.get(URL)

        assert response.status_code == 200
        body = response.json()
        assert body["projectName"] == "Acme Portal"
        assert body["stories"][0]["acceptanceCriteria"] == ["User can enter credentials"]

    def test_response_identifies_no_user_workspace_or_client(self, client: TestClient, client_review_response):
        with patch(USE_CASE, new=AsyncMock(return_value=client_review_response)):
            body = client.get(URL).json()

        assert set(body) == {"projectName", "phase", "total", "stories"}
        assert not {"createdBy", "assignedTo", "projectId", "clientName"} & set(body["stories"][0])

    def test_passes_pagination_through(self, client: TestClient, client_review_response):
        with patch(USE_CASE, new=AsyncMock(return_value=client_review_response)) as execute:
            client.get(URL, params={"limit": 20, "offset": 40})

        execute.assert_awaited_once_with(access_code=ACCESS_CODE, limit=20, offset=40)

    def test_an_unknown_code_returns_a_uniform_404(self, client: TestClient):
        with patch(USE_CASE, new=AsyncMock(side_effect=ProjectNotFoundError("access code"))):
            response = client.get(URL)

        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"

    @pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
    def test_invalid_pagination_returns_422(self, client: TestClient, params):
        assert client.get(URL, params=params).status_code == 422

    def test_is_rate_limited(self, client: TestClient):
        with patch(USE_CASE, new=AsyncMock(side_effect=ProjectNotFoundError("access code"))):
            statuses = [client.get(URL).status_code for _ in range(31)]

        assert statuses[:30] == [404] * 30
        assert statuses[30] == 429
