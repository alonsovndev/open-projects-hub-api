"""
Tests for ListProjectsUseCase.

Tests project listing with pagination and filtering.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestListProjectsUseCase:
    """Test ListProjectsUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_returns_list_of_projects(self):
        """Test successful project listing."""
        mock_repo = AsyncMock()

        project1 = ProjectEntity(
            id=EntityId.generate(),
            name="Project 1",
            code="PRJ1",
            description="Description 1",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        project2 = ProjectEntity(
            id=EntityId.generate(),
            name="Project 2",
            code="PRJ2",
            description="Description 2",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
            status=ProjectStatus.COMPLETED,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        mock_repo.count.return_value = 2
        mock_repo.find_all.return_value = [(project1, "Client 1"), (project2, "Client 2")]
        mock_repo.get_story_counts_batch.return_value = {}

        use_case = ListProjectsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user")

        assert isinstance(result, PaginatedResponse)
        assert result.total == 2
        assert result.page == 1
        assert result.per_page == 20
        assert len(result.items) == 2
        assert all(isinstance(p, ProjectResponse) for p in result.items)
        assert result.items[0].name == "Project 1"
        assert result.items[1].name == "Project 2"
        mock_repo.count.assert_called_once_with(status=None)
        mock_repo.find_all.assert_called_once_with(limit=20, offset=0, status=None)

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self):
        """Test project listing with pagination parameters."""
        mock_repo = AsyncMock()
        mock_repo.count.return_value = 100
        mock_repo.find_all.return_value = []
        mock_repo.get_story_counts_batch.return_value = {}

        use_case = ListProjectsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user", limit=10, offset=20)

        assert isinstance(result, PaginatedResponse)
        assert result.total == 100
        assert result.page == 3
        assert result.per_page == 10
        assert len(result.items) == 0
        mock_repo.count.assert_called_once_with(status=None)
        mock_repo.find_all.assert_called_once_with(limit=10, offset=20, status=None)

    @pytest.mark.asyncio
    async def test_execute_with_status_filter(self):
        """Test project listing with status filter."""
        mock_repo = AsyncMock()

        active_project = ProjectEntity(
            id=EntityId.generate(),
            name="Active Project",
            code="ACT1",
            description=None,
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        mock_repo.count.return_value = 1
        mock_repo.find_all.return_value = [(active_project, "Client")]
        mock_repo.get_story_counts_batch.return_value = {}

        use_case = ListProjectsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user", status="active")

        assert isinstance(result, PaginatedResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].status == "active"
        mock_repo.count.assert_called_once_with(status="active")
        mock_repo.find_all.assert_called_once_with(limit=20, offset=0, status="active")

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list_when_no_projects(self):
        """Test that empty result returns empty paginated response."""
        mock_repo = AsyncMock()
        mock_repo.count.return_value = 0
        mock_repo.find_all.return_value = []
        mock_repo.get_story_counts_batch.return_value = {}

        use_case = ListProjectsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user")

        assert isinstance(result, PaginatedResponse)
        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self):
        """Test project listing with all parameters."""
        mock_repo = AsyncMock()
        mock_repo.count.return_value = 200
        mock_repo.find_all.return_value = []
        mock_repo.get_story_counts_batch.return_value = {}

        use_case = ListProjectsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user", limit=50, offset=100, status="completed")

        assert isinstance(result, PaginatedResponse)
        assert result.total == 200
        assert result.page == 3
        assert result.per_page == 50
        mock_repo.count.assert_called_once_with(status="completed")
        mock_repo.find_all.assert_called_once_with(limit=50, offset=100, status="completed")

    @pytest.mark.asyncio
    async def test_execute_maps_all_entity_fields(self):
        """Test that all entity fields are correctly mapped to response."""
        mock_repo = AsyncMock()

        project = ProjectEntity(
            id=EntityId.generate(),
            name="Full Project",
            code="FULL",
            description="Complete Description",
            created_by=EntityId.generate(),
            client_id=EntityId.generate(),
            status=ProjectStatus.ARCHIVED,
            priority=ProjectPriority.HIGH,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )

        mock_repo.count.return_value = 1
        mock_repo.find_all.return_value = [(project, "Client")]
        mock_repo.get_story_counts_batch.return_value = {}

        use_case = ListProjectsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user")

        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 1
        assert result.items[0].id == str(project.id.value)
        assert result.items[0].name == "Full Project"
        assert result.items[0].description == "Complete Description"
        assert result.items[0].status == "archived"
        assert result.items[0].created_by == str(project.created_by.value)
