"""
Tests for ReactivateProjectUseCase.

Tests project reactivation including error handling.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.use_cases.reactivate_project import ReactivateProjectUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


class TestReactivateProjectUseCase:
    """Test ReactivateProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_reactivates_archived_project(self):
        """Test that an archived project is successfully reactivated."""
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        entity = ProjectEntity(
            id=project_id,
            name="Archived Project",
            code="ARC",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ARCHIVED,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.find_by_id.return_value = (entity, "Test Client")
        mock_repo.save.return_value = entity
        mock_repo.get_story_counts.return_value = (3, 1)
        mock_repo.count_active_by_workspace.return_value = 0

        use_case = ReactivateProjectUseCase(mock_repo)
        result = await use_case.execute(
            project_id=str(project_id.value), ctx=make_request_context(user_id=str(created_by.value))
        )

        assert isinstance(result, ProjectResponse)
        assert result.status == "active"
        assert entity.status == ProjectStatus.ACTIVE
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_reactivates_completed_project(self):
        """Test that a completed project can be reactivated."""
        mock_repo = AsyncMock()
        project_id = EntityId.generate()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        entity = ProjectEntity(
            id=project_id,
            name="Completed Project",
            code="CMP",
            description=None,
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.COMPLETED,
            priority=ProjectPriority.LOW,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repo.find_by_id.return_value = (entity, "Test Client")
        mock_repo.save.return_value = entity
        mock_repo.get_story_counts.return_value = (0, 0)
        mock_repo.count_active_by_workspace.return_value = 0

        use_case = ReactivateProjectUseCase(mock_repo)
        result = await use_case.execute(
            project_id=str(project_id.value), ctx=make_request_context(user_id=str(created_by.value))
        )

        assert result.status == "active"
        assert entity.status == ProjectStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_execute_raises_not_found_when_project_missing(self):
        """Test that reactivating a non-existent project raises ProjectNotFoundError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = ReactivateProjectUseCase(mock_repo)

        with pytest.raises(ProjectNotFoundError, match="Project not found"):
            await use_case.execute(project_id=str(uuid4()), ctx=make_request_context())

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_uuid(self):
        """Test that an invalid UUID string raises ValueError."""
        mock_repo = AsyncMock()
        use_case = ReactivateProjectUseCase(mock_repo)

        with pytest.raises(ValueError):
            await use_case.execute(project_id="not-a-valid-uuid", ctx=make_request_context())

        mock_repo.find_by_id.assert_not_called()
