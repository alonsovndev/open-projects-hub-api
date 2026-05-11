"""
Tests for UpdateProjectUseCase.

Tests project update including validation and error handling.
"""
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestUpdateProjectUseCase:
    """Test UpdateProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_updates_project_name(self):
        """Test updating project name."""
        # Setup
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        
        existing_entity = ProjectEntity(
            id=project_id,
            name="Old Name",
            description="Description",
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = existing_entity
        
        use_case = UpdateProjectUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(
            project_id=str(project_id.value),
            name="New Name",
        )
        
        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.name == "New Name"
        mock_repo.find_by_id.assert_called_once()
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_updates_multiple_fields(self):
        """Test updating multiple project fields at once."""
        # Setup
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        
        existing_entity = ProjectEntity(
            id=project_id,
            name="Old Name",
            description="Old Description",
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = existing_entity
        
        use_case = UpdateProjectUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(
            project_id=str(project_id.value),
            name="New Name",
            description="New Description",
            status="completed",
        )
        
        # Assert
        assert result.name == "New Name"
        assert result.description == "New Description"
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_project_not_found(self):
        """Test that non-existent project returns None."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        
        use_case = UpdateProjectUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(
            project_id=str(uuid4()),
            name="New Name",
        )
        
        # Assert
        assert result is None
        mock_repo.find_by_id.assert_called_once()
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_updates_dates(self):
        """Test updating project dates."""
        # Setup
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        
        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            description=None,
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = existing_entity
        
        use_case = UpdateProjectUseCase(mock_repo)
        
        new_start = date(2026, 6, 1)
        new_end = date(2026, 12, 31)
        
        # Execute
        result = await use_case.execute(
            project_id=str(project_id.value),
            start_date=new_start,
            end_date=new_end,
        )
        
        # Assert
        assert result.start_date == new_start
        assert result.end_date == new_end

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_dates(self):
        """Test that invalid dates raise ValueError."""
        # Setup
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        
        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            description=None,
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=date(2026, 5, 1),
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_entity
        
        use_case = UpdateProjectUseCase(mock_repo)
        
        # Execute & Assert
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            await use_case.execute(
                project_id=str(project_id.value),
                end_date=date(2026, 4, 1),
            )

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that save failure raises ValueError."""
        # Setup
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        
        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            description=None,
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = None
        
        use_case = UpdateProjectUseCase(mock_repo)
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Failed to update project"):
            await use_case.execute(
                project_id=str(project_id.value),
                name="New Name",
            )

    @pytest.mark.asyncio
    async def test_execute_converts_status_string_to_enum(self):
        """Test that status string is correctly converted to enum."""
        # Setup
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        
        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            description=None,
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.find_by_id.return_value = existing_entity
        mock_repo.save.return_value = existing_entity
        
        use_case = UpdateProjectUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(
            project_id=str(project_id.value),
            status="archived",
        )
        
        # Assert
        assert result.status == "archived"
        assert existing_entity.status == ProjectStatus.ARCHIVED
