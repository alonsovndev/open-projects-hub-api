"""
Tests for active-project limit enforcement.

Covers:
- Create blocked when admin is at the active-project limit
- Create allowed when admin is below the limit
- Create allowed after archiving (archived projects don't count)
- Reactivate blocked at the limit
- Reactivate allowed below the limit
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.app.features.projects.application.dtos.project_dto import CreateProjectRequest, ProjectResponse
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.application.use_cases.reactivate_project import ReactivateProjectUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ActiveProjectLimitExceededError
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId


def _build_entity(status: ProjectStatus) -> ProjectEntity:
    """Build a project entity with the given status."""
    return ProjectEntity(
        id=EntityId.generate(),
        name="Project",
        code="PRJ",
        description=None,
        created_by=EntityId.generate(),
        client_id=EntityId.generate(),
        status=status,
        priority=ProjectPriority.MEDIUM,
        start_date=None,
        end_date=None,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


class TestActiveProjectLimitCreate:
    """Test limit enforcement on project creation."""

    @pytest.mark.asyncio
    async def test_create_blocked_at_limit(self):
        """Admin with 3 active projects cannot create a 4th."""
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        mock_project_repo.count_active_by_user.return_value = 3

        client_id = EntityId.generate()
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo, max_active_projects=3)
        request = CreateProjectRequest(
            name="New Project",
            code="NEW",
            client_id=str(client_id.value),
        )

        with pytest.raises(ActiveProjectLimitExceededError):
            await use_case.execute(request=request, created_by=str(EntityId.generate().value))

        mock_project_repo.save.assert_not_called()
        mock_client_repo.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_allowed_below_limit(self):
        """Admin with 2 active projects can create a 3rd."""
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        mock_project_repo.count_active_by_user.return_value = 2
        mock_project_repo.save.return_value = _build_entity(ProjectStatus.ACTIVE)

        client_id = EntityId.generate()
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo, max_active_projects=3)
        request = CreateProjectRequest(
            name="New Project",
            code="NEW",
            client_id=str(client_id.value),
        )

        result = await use_case.execute(request=request, created_by=str(EntityId.generate().value))

        assert isinstance(result, ProjectResponse)
        mock_project_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_allowed_when_count_indicates_archived_excluded(self):
        """Archived projects do not count: admin archiving frees a slot."""
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        # count_active_by_user only counts ACTIVE projects (archived excluded)
        mock_project_repo.count_active_by_user.return_value = 2
        mock_project_repo.save.return_value = _build_entity(ProjectStatus.ACTIVE)

        client_id = EntityId.generate()
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo, max_active_projects=3)
        request = CreateProjectRequest(
            name="New Project",
            code="NEW",
            client_id=str(client_id.value),
        )

        result = await use_case.execute(request=request, created_by=str(EntityId.generate().value))

        assert isinstance(result, ProjectResponse)
        mock_project_repo.save.assert_called_once()


class TestActiveProjectLimitReactivate:
    """Test limit enforcement on project reactivation."""

    @pytest.mark.asyncio
    async def test_reactivate_blocked_at_limit(self):
        """Admin with 3 active projects cannot reactivate an archived one."""
        mock_repo = AsyncMock()
        archived = _build_entity(ProjectStatus.ARCHIVED)
        mock_repo.find_by_id.return_value = (archived, "Test Client")
        mock_repo.count_active_by_user.return_value = 3

        use_case = ReactivateProjectUseCase(mock_repo, max_active_projects=3)

        with pytest.raises(ActiveProjectLimitExceededError):
            await use_case.execute(
                project_id=str(EntityId.generate().value),
                created_by=str(EntityId.generate().value),
            )

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_reactivate_allowed_below_limit(self):
        """Admin with 2 active projects can reactivate an archived one."""
        mock_repo = AsyncMock()
        archived = _build_entity(ProjectStatus.ARCHIVED)
        mock_repo.find_by_id.return_value = (archived, "Test Client")
        mock_repo.count_active_by_user.return_value = 2
        mock_repo.save.return_value = archived
        mock_repo.get_story_counts.return_value = (0, 0)

        use_case = ReactivateProjectUseCase(mock_repo, max_active_projects=3)

        result = await use_case.execute(
            project_id=str(archived.id.value),
            created_by=str(archived.created_by.value),
        )

        assert isinstance(result, ProjectResponse)
        assert result.status == "active"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_reactivate_already_active_skips_limit_check(self):
        """Reactivating an already-active project does not re-check the limit."""
        mock_repo = AsyncMock()
        active = _build_entity(ProjectStatus.ACTIVE)
        mock_repo.find_by_id.return_value = (active, "Test Client")
        mock_repo.save.return_value = active
        mock_repo.get_story_counts.return_value = (0, 0)

        use_case = ReactivateProjectUseCase(mock_repo, max_active_projects=3)

        result = await use_case.execute(
            project_id=str(active.id.value),
            created_by=str(active.created_by.value),
        )

        assert isinstance(result, ProjectResponse)
        mock_repo.count_active_by_user.assert_not_called()
        mock_repo.save.assert_called_once()
