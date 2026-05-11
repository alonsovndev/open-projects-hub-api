"""
Tests for ListProjectsUseCase.

Tests project listing with pagination and filtering.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestListProjectsUseCase:
    """Test ListProjectsUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_returns_list_of_projects(self):
        """Test successful project listing."""
        # Setup
        mock_repo = AsyncMock()
        
        project1 = ProjectEntity(
            id=EntityId.generate(),
            name="Project 1",
            description="Description 1",
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        project2 = ProjectEntity(
            id=EntityId.generate(),
            name="Project 2",
            description="Description 2",
            created_by=EntityId.generate(),
            status=ProjectStatus.COMPLETED,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_repo.find_all.return_value = [project1, project2]
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute()
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, ProjectResponse) for p in result)
        assert result[0].name == "Project 1"
        assert result[1].name == "Project 2"
        mock_repo.find_all.assert_called_once_with(limit=20, offset=0, status=None)

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self):
        """Test project listing with pagination parameters."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(limit=10, offset=20)
        
        # Assert
        assert isinstance(result, list)
        mock_repo.find_all.assert_called_once_with(limit=10, offset=20, status=None)

    @pytest.mark.asyncio
    async def test_execute_with_status_filter(self):
        """Test project listing with status filter."""
        # Setup
        mock_repo = AsyncMock()
        
        active_project = ProjectEntity(
            id=EntityId.generate(),
            name="Active Project",
            description=None,
            created_by=EntityId.generate(),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_repo.find_all.return_value = [active_project]
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(status="active")
        
        # Assert
        assert len(result) == 1
        assert result[0].status == "active"
        mock_repo.find_all.assert_called_once_with(limit=20, offset=0, status="active")

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list_when_no_projects(self):
        """Test that empty result returns empty list."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute()
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self):
        """Test project listing with all parameters."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Execute
        await use_case.execute(limit=50, offset=100, status="completed")
        
        # Assert
        mock_repo.find_all.assert_called_once_with(
            limit=50,
            offset=100,
            status="completed"
        )

    @pytest.mark.asyncio
    async def test_execute_maps_all_entity_fields(self):
        """Test that all entity fields are correctly mapped to response."""
        # Setup
        mock_repo = AsyncMock()
        
        project = ProjectEntity(
            id=EntityId.generate(),
            name="Full Project",
            description="Complete Description",
            created_by=EntityId.generate(),
            status=ProjectStatus.ARCHIVED,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        mock_repo.find_all.return_value = [project]
        
        use_case = ListProjectsUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute()
        
        # Assert
        assert result[0].id == str(project.id.value)
        assert result[0].name == "Full Project"
        assert result[0].description == "Complete Description"
        assert result[0].status == "archived"
        assert result[0].created_by == str(project.created_by.value)
