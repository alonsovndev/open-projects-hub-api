"""
Tests for CreateProjectUseCase.

Tests project creation including validation and error handling.
"""
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestCreateProjectUseCase:
    """Test CreateProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_creates_project_successfully(self):
        """Test successful project creation with minimal fields."""
        # Setup
        mock_repo = AsyncMock()
        created_by = EntityId.generate()
        
        created_entity = ProjectEntity(
            id=EntityId.generate(),
            name="New Project",
            description=None,
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.save.return_value = created_entity
        
        use_case = CreateProjectUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(
            name="New Project",
            created_by=str(created_by.value),
        )
        
        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.name == "New Project"
        assert result.status == "active"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_creates_project_with_all_fields(self):
        """Test project creation with all optional fields."""
        # Setup
        mock_repo = AsyncMock()
        created_by = EntityId.generate()
        start = date(2026, 5, 1)
        end = date(2026, 12, 31)
        
        created_entity = ProjectEntity(
            id=EntityId.generate(),
            name="Full Project",
            description="A complete project",
            created_by=created_by,
            status=ProjectStatus.ACTIVE,
            start_date=start,
            end_date=end,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.save.return_value = created_entity
        
        use_case = CreateProjectUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(
            name="Full Project",
            created_by=str(created_by.value),
            description="A complete project",
            start_date=start,
            end_date=end,
        )
        
        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.name == "Full Project"
        assert result.description == "A complete project"
        assert result.start_date == start
        assert result.end_date == end
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_name(self):
        """Test that empty name raises ValueError."""
        # Setup
        mock_repo = AsyncMock()
        use_case = CreateProjectUseCase(mock_repo)
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            await use_case.execute(
                name="",
                created_by=str(uuid4()),
            )
        
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_dates(self):
        """Test that end date before start date raises ValueError."""
        # Setup
        mock_repo = AsyncMock()
        use_case = CreateProjectUseCase(mock_repo)
        
        # Execute & Assert
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            await use_case.execute(
                name="Project",
                created_by=str(uuid4()),
                start_date=date(2026, 12, 31),
                end_date=date(2026, 5, 1),
            )
        
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that save failure raises ValueError."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.save.return_value = None
        
        use_case = CreateProjectUseCase(mock_repo)
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Failed to create project"):
            await use_case.execute(
                name="Project",
                created_by=str(uuid4()),
            )
        
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parses_created_by_uuid(self):
        """Test that created_by string is correctly parsed to EntityId."""
        # Setup
        mock_repo = AsyncMock()
        created_by_uuid = uuid4()
        
        created_entity = ProjectEntity(
            id=EntityId.generate(),
            name="Test Project",
            description=None,
            created_by=EntityId.from_string(str(created_by_uuid)),
            status=ProjectStatus.ACTIVE,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repo.save.return_value = created_entity
        
        use_case = CreateProjectUseCase(mock_repo)
        
        # Execute
        result = await use_case.execute(
            name="Test Project",
            created_by=str(created_by_uuid),
        )
        
        # Assert
        assert result.created_by == str(created_by_uuid)
        
        # Verify the entity passed to save has correct created_by
        save_call_args = mock_repo.save.call_args[0][0]
        assert save_call_args.created_by.value == created_by_uuid
