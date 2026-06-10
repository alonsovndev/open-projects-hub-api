"""
Tests for UpdateProjectUseCase.

Tests project update including validation and error handling.
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.app.features.projects.application.dtos.project_dto import ProjectResponse, UpdateProjectRequest
from src.app.features.projects.application.use_cases.update_project import UpdateProjectUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestUpdateProjectUseCase:
    """Test UpdateProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_updates_project_name(self):
        """Test updating project name."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        existing_entity = ProjectEntity(
            id=project_id,
            name="Old Name",
            code="OLD",
            description="Description",
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = (existing_entity, "Test Client")
        mock_repo.save.return_value = existing_entity
        mock_repo.get_story_counts.return_value = (0, 0)

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        request = UpdateProjectRequest(name="New Name")
        result = await use_case.execute(
            project_id=str(project_id.value),
            request=request,
            created_by="test-user",
        )

        assert isinstance(result, ProjectResponse)
        assert result.name == "New Name"
        mock_repo.find_by_id.assert_called_once()
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_updates_multiple_fields(self):
        """Test updating multiple project fields at once."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        existing_entity = ProjectEntity(
            id=project_id,
            name="Old Name",
            code="OLD",
            description="Old Description",
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = (existing_entity, "Test Client")
        mock_repo.save.return_value = existing_entity
        mock_repo.get_story_counts.return_value = (0, 0)

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        request = UpdateProjectRequest(
            name="New Name",
            description="New Description",
            status="completed",
        )
        result = await use_case.execute(
            project_id=str(project_id.value),
            request=request,
            created_by="test-user",
        )

        assert result.name == "New Name"
        assert result.description == "New Description"
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_project_not_found(self):
        """Test that non-existent project returns None."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        request = UpdateProjectRequest(name="New Name")
        result = await use_case.execute(
            project_id=str(uuid4()),
            request=request,
            created_by="test-user",
        )

        assert result is None
        mock_repo.find_by_id.assert_called_once()
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_updates_dates(self):
        """Test updating project dates."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            code="PRJ",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = (existing_entity, "Test Client")
        mock_repo.save.return_value = existing_entity
        mock_repo.get_story_counts.return_value = (0, 0)

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        new_start = date(2026, 6, 1)
        new_end = date(2026, 12, 31)

        request = UpdateProjectRequest(start_date=new_start, end_date=new_end)
        result = await use_case.execute(
            project_id=str(project_id.value),
            request=request,
            created_by="test-user",
        )

        assert result.start_date == new_start
        assert result.end_date == new_end

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_dates(self):
        """Test that invalid dates raise ValueError."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            code="PRJ",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=date(2026, 5, 1),
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = (existing_entity, "Test Client")

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        request = UpdateProjectRequest(end_date=date(2026, 4, 1))
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            await use_case.execute(
                project_id=str(project_id.value),
                request=request,
                created_by="test-user",
            )

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that save failure raises ValueError."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            code="PRJ",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = (existing_entity, "Test Client")
        mock_repo.save.return_value = None

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        request = UpdateProjectRequest(name="New Name")
        with pytest.raises(ValueError, match="Failed to update project"):
            await use_case.execute(
                project_id=str(project_id.value),
                request=request,
                created_by="test-user",
            )

    @pytest.mark.asyncio
    async def test_execute_converts_status_string_to_enum(self):
        """Test that status string is correctly converted to enum."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            code="PRJ",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = (existing_entity, "Test Client")
        mock_repo.save.return_value = existing_entity
        mock_repo.get_story_counts.return_value = (0, 0)

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        request = UpdateProjectRequest(status="archived")
        result = await use_case.execute(
            project_id=str(project_id.value),
            request=request,
            created_by="test-user",
        )

        assert result.status == "archived"
        assert existing_entity.status == ProjectStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_execute_raises_validation_error_on_invalid_status(self):
        """Test that invalid status raises ValidationError at DTO level."""
        with pytest.raises(ValidationError, match="Status must be one of"):
            UpdateProjectRequest(status="invalid_status")

    @pytest.mark.asyncio
    async def test_execute_verifies_client_exists_when_changing_client(self):
        """Test that changing client verifies the new client exists."""
        mock_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()
        new_client_id = EntityId.generate()

        existing_entity = ProjectEntity(
            id=project_id,
            name="Project",
            code="PRJ",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.find_by_id.return_value = (existing_entity, "Old Client")

        mock_client_repo.find_by_id.return_value = None

        use_case = UpdateProjectUseCase(mock_repo, mock_client_repo)

        request = UpdateProjectRequest(client_id=str(new_client_id.value))
        with pytest.raises(ValueError, match="Client not found"):
            await use_case.execute(
                project_id=str(project_id.value),
                request=request,
                created_by="test-user",
            )
