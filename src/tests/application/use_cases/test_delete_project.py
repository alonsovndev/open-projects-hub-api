"""
Tests for DeleteProjectUseCase.

Tests project deletion including error handling.
"""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.app.features.projects.application.use_cases.delete_project import DeleteProjectUseCase


class TestDeleteProjectUseCase:
    """Test DeleteProjectUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_deletes_project_successfully(self):
        """Test successful project deletion."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        
        use_case = DeleteProjectUseCase(mock_repo)
        project_id = uuid4()
        
        # Execute
        result = await use_case.execute(str(project_id))
        
        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(project_id)

    @pytest.mark.asyncio
    async def test_execute_returns_false_when_project_not_found(self):
        """Test that non-existent project returns False."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False
        
        use_case = DeleteProjectUseCase(mock_repo)
        project_id = uuid4()
        
        # Execute
        result = await use_case.execute(str(project_id))
        
        # Assert
        assert result is False
        mock_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parses_uuid_string_correctly(self):
        """Test that UUID string is correctly parsed."""
        # Setup
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        
        use_case = DeleteProjectUseCase(mock_repo)
        project_id = uuid4()
        
        # Execute
        await use_case.execute(str(project_id))
        
        # Assert - verify correct UUID was passed to delete
        called_with = mock_repo.delete.call_args[0][0]
        assert called_with == project_id

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_invalid_uuid(self):
        """Test that invalid UUID string raises ValueError."""
        # Setup
        mock_repo = AsyncMock()
        use_case = DeleteProjectUseCase(mock_repo)
        
        # Execute & Assert
        with pytest.raises(ValueError):
            await use_case.execute("not-a-valid-uuid")
        
        mock_repo.delete.assert_not_called()
