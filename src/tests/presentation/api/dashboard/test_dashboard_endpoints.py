"""Integration tests for dashboard endpoints."""
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.app.app import fastApiApp
from src.app.config.app_config import AppConfig
from src.app.features.dashboard.application.dtos.dashboard_dto import DashboardStatsResponse
from src.app.features.dashboard.application.dtos.dashboard_dto import ProjectSummary, StorySummary
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
def user_token(app_jwt_handler):
    """Generate user JWT token for tests."""
    return app_jwt_handler.create_access_token(
        user_id="550e8400-e29b-41d4-a716-446655440001",
        email="user@example.com",
        role="viewer",
    )


@pytest.fixture
def mock_dashboard_stats():
    """Create mock dashboard stats response."""
    return DashboardStatsResponse(
        total_projects=5,
        active_projects=3,
        total_stories=42,
        assigned_stories=12,
        completed_stories=18,
        recent_projects=[
            ProjectSummary(
                id="550e8400-e29b-41d4-a716-446655440001",
                name="Project 1",
                status="active",
                created_at="2026-05-09T12:00:00",
            )
        ],
        recent_stories=[
            StorySummary(
                id="550e8400-e29b-41d4-a716-446655440100",
                title="Story 1",
                status="todo",
                priority="high",
                created_at="2026-05-09T12:00:00",
            )
        ],
    )


class TestGetDashboardStatsEndpoint:
    """Test GET /v1/dashboard/stats endpoint."""
    
    def test_get_dashboard_stats_success(self, client: TestClient, user_token: str, mock_dashboard_stats):
        """Test getting dashboard stats returns stats data."""
        with patch(
            "src.app.features.dashboard.application.use_cases.get_dashboard_stats.GetDashboardStatsUseCase.execute",
            new=AsyncMock(return_value=mock_dashboard_stats),
        ):
            response = client.get(
                "/v1/dashboard/stats",
                headers={"Authorization": f"Bearer {user_token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["totalProjects"] == 5
        assert data["activeProjects"] == 3
        assert data["totalStories"] == 42
        assert data["assignedStories"] == 12
        assert data["completedStories"] == 18
        assert len(data["recentProjects"]) == 1
        assert len(data["recentStories"]) == 1
    
    def test_get_dashboard_stats_unauthorized_without_token(self, client: TestClient):
        """Test getting dashboard stats without token returns 403."""
        response = client.get("/v1/dashboard/stats")
        
        assert response.status_code == 403
    
    def test_get_dashboard_stats_with_empty_stats(self, client: TestClient, user_token: str):
        """Test getting dashboard stats with no data."""
        empty_stats = DashboardStatsResponse(
            total_projects=0,
            active_projects=0,
            total_stories=0,
            assigned_stories=0,
            completed_stories=0,
            recent_projects=[],
            recent_stories=[],
        )
        with patch(
            "src.app.features.dashboard.application.use_cases.get_dashboard_stats.GetDashboardStatsUseCase.execute",
            new=AsyncMock(return_value=empty_stats),
        ):
            response = client.get(
                "/v1/dashboard/stats",
                headers={"Authorization": f"Bearer {user_token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["totalProjects"] == 0
        assert data["activeProjects"] == 0
        assert data["totalStories"] == 0
        assert data["assignedStories"] == 0
        assert data["completedStories"] == 0
        assert data["recentProjects"] == []
        assert data["recentStories"] == []
    
    def test_get_dashboard_stats_invalid_token(self, client: TestClient):
        """Test getting dashboard stats with invalid token returns 401."""
        response = client.get(
            "/v1/dashboard/stats",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        
        assert response.status_code == 401
    
    def test_get_dashboard_stats_with_multiple_projects(self, client: TestClient, user_token: str):
        """Test getting dashboard stats with multiple projects."""
        multi_stats = DashboardStatsResponse(
            total_projects=10,
            active_projects=7,
            total_stories=100,
            assigned_stories=25,
            completed_stories=50,
            recent_projects=[
                ProjectSummary(
                    id=f"550e8400-e29b-41d4-a716-44665544000{i}",
                    name=f"Project {i}",
                    status="active",
                    created_at="2026-05-09T12:00:00",
                )
                for i in range(5)
            ],
            recent_stories=[
                StorySummary(
                    id=f"550e8400-e29b-41d4-a716-44665544020{i}",
                    title=f"Story {i}",
                    status="todo",
                    priority="high",
                    created_at="2026-05-09T12:00:00",
                )
                for i in range(5)
            ],
        )
        with patch(
            "src.app.features.dashboard.application.use_cases.get_dashboard_stats.GetDashboardStatsUseCase.execute",
            new=AsyncMock(return_value=multi_stats),
        ):
            response = client.get(
                "/v1/dashboard/stats",
                headers={"Authorization": f"Bearer {user_token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["totalProjects"] == 10
        assert data["activeProjects"] == 7
        assert data["totalStories"] == 100
        assert len(data["recentProjects"]) == 5
        assert len(data["recentStories"]) == 5