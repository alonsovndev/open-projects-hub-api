"""
Tests for CreateProjectUseCase.

Tests project creation including validation and error handling.
"""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.projects.application.dtos.project_dto import CreateProjectRequest, ProjectResponse
from src.app.features.projects.application.use_cases.create_project import CreateProjectUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError, ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


class TestCreateProjectUseCase:
    """Test CreateProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_creates_project_successfully(self):
        """Test successful project creation with minimal fields."""
        # Setup
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        mock_project_repo.count_active_by_workspace.return_value = 0

        # Mock client lookup
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        created_entity = ProjectEntity(
            id=EntityId.generate(),
            name="New Project",
            code="NEW",
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
        mock_project_repo.save.return_value = created_entity

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo)

        request = CreateProjectRequest(
            name="New Project",
            code="NEW",
            client_id=str(client_id.value),
            phase="discovery",
        )

        # Execute
        result = await use_case.execute(
            request=request,
            ctx=make_request_context(user_id=str(created_by.value)),
        )

        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.name == "New Project"
        assert result.status == "active"
        mock_project_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_creates_project_with_all_fields(self):
        """Test project creation with all optional fields."""
        # Setup
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        created_by = EntityId.generate()
        client_id = EntityId.generate()
        start = date(2026, 5, 1)
        end = date(2026, 12, 31)

        mock_project_repo.count_active_by_workspace.return_value = 0

        # Mock client lookup
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        created_entity = ProjectEntity(
            id=EntityId.generate(),
            name="Full Project",
            code="FULL",
            description="A complete project",
            created_by=created_by,
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.HIGH,
            start_date=start,
            end_date=end,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_project_repo.save.return_value = created_entity

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo)

        request = CreateProjectRequest(
            name="Full Project",
            code="FULL",
            client_id=str(client_id.value),
            phase="discovery",
            description="A complete project",
            priority="high",
            start_date=start,
            end_date=end,
        )

        # Execute
        result = await use_case.execute(
            request=request,
            ctx=make_request_context(user_id=str(created_by.value)),
        )

        # Assert
        assert isinstance(result, ProjectResponse)
        assert result.name == "Full Project"
        assert result.description == "A complete project"
        assert result.start_date == start
        assert result.end_date == end
        mock_project_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_name(self):
        """Test that empty name raises ValidationError at DTO level."""
        # Setup
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        client_id = EntityId.generate()

        # Mock client lookup
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            CreateProjectRequest(
                name="",
                code="TEST",
                client_id=str(client_id.value),
                phase="discovery",
            )

        mock_project_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_dates(self):
        """Test that end date before start date raises ValidationError at DTO level."""
        # Setup
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        client_id = EntityId.generate()

        # Mock client lookup
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        with pytest.raises(ValidationError, match="End date cannot be before start date"):
            CreateProjectRequest(
                name="Project",
                code="TEST",
                client_id=str(client_id.value),
                phase="discovery",
                start_date=date(2026, 12, 31),
                end_date=date(2026, 5, 1),
            )

        mock_project_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that save failure raises ValueError."""
        # Setup
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        client_id = EntityId.generate()

        mock_project_repo.count_active_by_workspace.return_value = 0

        # Mock client lookup
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        mock_project_repo.save.return_value = None

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo)

        request = CreateProjectRequest(
            name="Project",
            code="TEST",
            client_id=str(client_id.value),
            phase="discovery",
        )

        # Execute & Assert
        with pytest.raises(RuntimeError, match="Failed to create project"):
            await use_case.execute(
                request=request,
                ctx=make_request_context(user_id=str(uuid4())),
            )

        mock_project_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parses_created_by_uuid(self):
        """Test that created_by string is correctly parsed to EntityId."""
        # Setup
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        created_by_uuid = uuid4()
        client_id = EntityId.generate()

        mock_project_repo.count_active_by_workspace.return_value = 0

        # Mock client lookup
        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        created_entity = ProjectEntity(
            id=EntityId.generate(),
            name="Test Project",
            code="TEST",
            description=None,
            created_by=EntityId.from_string(str(created_by_uuid)),
            client_id=client_id,
            status=ProjectStatus.ACTIVE,
            priority=ProjectPriority.MEDIUM,
            start_date=None,
            end_date=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_project_repo.save.return_value = created_entity

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo)

        request = CreateProjectRequest(
            name="Test Project",
            code="TEST",
            client_id=str(client_id.value),
            phase="discovery",
        )

        # Execute
        result = await use_case.execute(
            request=request,
            ctx=make_request_context(user_id=str(created_by_uuid)),
        )

        # Assert
        assert result.created_by == str(created_by_uuid)

        # Verify the entity passed to save has correct created_by
        save_call_args = mock_project_repo.save.call_args[0][0]
        assert save_call_args.created_by.value == created_by_uuid

    @pytest.mark.asyncio
    async def test_execute_raises_validation_error_on_invalid_phase(self):
        """Test that a phase outside discovery/planning raises ValidationError at DTO level."""
        client_id = EntityId.generate()

        with pytest.raises(ValidationError, match="Phase must be one of"):
            CreateProjectRequest(
                name="Project",
                code="TEST",
                client_id=str(client_id.value),
                phase="delivery",
            )

    @pytest.mark.asyncio
    async def test_execute_persists_requested_phase(self):
        """Test that the requested phase is passed through to the created entity."""
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        created_by = EntityId.generate()
        client_id = EntityId.generate()

        mock_project_repo.count_active_by_workspace.return_value = 0

        mock_client = AsyncMock()
        mock_client.name = "Test Client"
        mock_client_repo.find_by_id.return_value = mock_client

        async def _save(entity: ProjectEntity) -> ProjectEntity:
            return entity

        mock_project_repo.save.side_effect = _save

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo)

        request = CreateProjectRequest(
            name="Planning Project",
            code="PLAN",
            client_id=str(client_id.value),
            phase="planning",
        )

        result = await use_case.execute(request=request, ctx=make_request_context(user_id=str(created_by.value)))

        assert result.phase == "planning"

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_client_not_found(self):
        """Test that non-existent client raises NotFoundError."""
        # Setup
        mock_project_repo = AsyncMock()
        mock_client_repo = AsyncMock()
        mock_client_repo.find_by_id.return_value = None

        mock_project_repo.count_active_by_workspace.return_value = 0

        use_case = CreateProjectUseCase(mock_project_repo, mock_client_repo)

        request = CreateProjectRequest(
            name="Project",
            code="TEST",
            client_id=str(uuid4()),
            phase="discovery",
        )

        # Execute & Assert
        with pytest.raises(NotFoundError, match=r"Client.*not found"):
            await use_case.execute(
                request=request,
                ctx=make_request_context(user_id=str(uuid4())),
            )

        mock_project_repo.save.assert_not_called()
