"""
Tests for DeleteProjectUseCase.

Tests project deletion including error handling.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.tests.support.request_context import TEST_WORKSPACE_UUID, make_request_context


class TestDeleteProjectUseCase:
    """Test DeleteProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_deletes_project_successfully(self):
        """Test successful project deletion."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True

        use_case = DeleteProjectUseCase(mock_repo)
        project_id = uuid4()

        # Execute
        await use_case.execute(str(project_id), ctx=make_request_context())

        # Assert
        mock_repo.delete.assert_called_once_with(project_id, workspace_id=TEST_WORKSPACE_UUID)

    @pytest.mark.asyncio
    async def test_execute_raises_not_found_when_project_missing(self):
        """Test that non-existent project raises ProjectNotFoundError."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False

        use_case = DeleteProjectUseCase(mock_repo)
        project_id = uuid4()

        with pytest.raises(ProjectNotFoundError, match="Project not found"):
            await use_case.execute(str(project_id), ctx=make_request_context())

        mock_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parses_uuid_string_correctly(self):
        """Test that UUID string is correctly parsed."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True

        use_case = DeleteProjectUseCase(mock_repo)
        project_id = uuid4()

        await use_case.execute(str(project_id), ctx=make_request_context())

        called_with = mock_repo.delete.call_args[0][0]
        assert called_with == project_id

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_uuid(self):
        """Test that invalid UUID string raises ValueError."""
        mock_repo = AsyncMock()
        use_case = DeleteProjectUseCase(mock_repo)

        with pytest.raises(ValueError):
            await use_case.execute("not-a-valid-uuid", ctx=make_request_context())

        mock_repo.delete.assert_not_called()
