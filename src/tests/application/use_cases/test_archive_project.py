"""
Tests for ArchiveProjectUseCase.

Tests project archival including error handling.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.use_cases.archive_project import ArchiveProjectUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestArchiveProjectUseCase:
    """Test ArchiveProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_archives_active_project(self):
        """Test that an active project is successfully archived."""
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        entity = ProjectEntity(
            id=project_id,
            name="Active Project",
            code="ACT",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.find_by_id.return_value = (entity, "Test Client")
        mock_repo.save.return_value = entity
        mock_repo.get_story_counts.return_value = (5, 2)

        use_case = ArchiveProjectUseCase(mock_repo)
        result = await use_case.execute(project_id=str(project_id.value), created_by="test-user")

        assert isinstance(result, ProjectResponse)
        assert result.status == "archived"
        assert entity.status == ProjectStatus.ARCHIVED
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_not_found_when_project_missing(self):
        """Test that archiving a non-existent project raises ProjectNotFoundError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = ArchiveProjectUseCase(mock_repo)

        with pytest.raises(ProjectNotFoundError, match="Project not found"):
            await use_case.execute(project_id=str(uuid4()), created_by="test-user")

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_uuid(self):
        """Test that an invalid UUID string raises ValueError."""
        mock_repo = AsyncMock()
        use_case = ArchiveProjectUseCase(mock_repo)

        with pytest.raises(ValueError):
            await use_case.execute(project_id="not-a-valid-uuid", created_by="test-user")

        mock_repo.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_returns_response_with_story_counts(self):
        """Test that the response includes correct story counts."""
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        entity = ProjectEntity(
            id=project_id,
            name="Project",
            code="PRJ",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.COMPLETED,
            priority=ProjectPriority.HIGH,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.find_by_id.return_value = (entity, "Client X")
        mock_repo.save.return_value = entity
        mock_repo.get_story_counts.return_value = (10, 8)

        use_case = ArchiveProjectUseCase(mock_repo)
        result = await use_case.execute(project_id=str(project_id.value), created_by="test-user")

        assert result.stories_count == 10
        assert result.completed_stories == 8
