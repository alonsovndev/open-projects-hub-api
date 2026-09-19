"""Tests for DeleteClientUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.clients.application.use_cases.delete_client import DeleteClientUseCase
from src.app.features.clients.domain.exceptions.client_exceptions import (
    ClientHasActiveProjectsError,
    ClientNotFoundError,
)
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestDeleteClientUseCase:
    """Test DeleteClientUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_deletes_client_successfully(self):
        """Test successful client deletion."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_project_repo = AsyncMock()
        mock_project_repo.has_active_projects_for_client.return_value = False
        mock_project_repo.delete_archived_by_client.return_value = 0

        use_case = DeleteClientUseCase(mock_repo, mock_project_repo)

        client_id = EntityId.generate()

        result = await use_case.execute(client_id=client_id.value, created_by="test-user")

        assert result is True
        mock_repo.delete.assert_called_once_with(client_id.value)

    @pytest.mark.asyncio
    async def test_execute_deletes_archived_projects_before_client(self):
        """Test archived projects are deleted before the client itself."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_project_repo = AsyncMock()
        mock_project_repo.has_active_projects_for_client.return_value = False
        mock_project_repo.delete_archived_by_client.return_value = 2

        use_case = DeleteClientUseCase(mock_repo, mock_project_repo)

        client_id = EntityId.generate()

        await use_case.execute(client_id=client_id.value, created_by="test-user")

        mock_project_repo.delete_archived_by_client.assert_called_once_with(client_id.value)
        mock_repo.delete.assert_called_once_with(client_id.value)

    @pytest.mark.asyncio
    async def test_execute_blocked_when_client_has_active_projects(self):
        """Test deletion is blocked when the client has active projects."""
        mock_repo = AsyncMock()
        mock_project_repo = AsyncMock()
        mock_project_repo.has_active_projects_for_client.return_value = True

        use_case = DeleteClientUseCase(mock_repo, mock_project_repo)

        client_id = EntityId.generate()

        with pytest.raises(ClientHasActiveProjectsError, match="has active projects"):
            await use_case.execute(client_id=client_id.value, created_by="test-user")

        mock_repo.delete.assert_not_called()
        mock_project_repo.delete_archived_by_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_not_found_raises_client_not_found(self):
        """Test that non-existent client raises ClientNotFoundError."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False
        mock_project_repo = AsyncMock()
        mock_project_repo.has_active_projects_for_client.return_value = False
        mock_project_repo.delete_archived_by_client.return_value = 0

        use_case = DeleteClientUseCase(mock_repo, mock_project_repo)

        client_id = uuid4()

        with pytest.raises(ClientNotFoundError, match=f"Client not found: {client_id}"):
            await use_case.execute(client_id=client_id, created_by="test-user")
