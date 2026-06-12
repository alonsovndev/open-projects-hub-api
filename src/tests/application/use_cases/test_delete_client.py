"""Tests for DeleteClientUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.clients.application.use_cases.delete_client import DeleteClientUseCase
from src.app.features.clients.domain.exceptions.client_exceptions import ClientNotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestDeleteClientUseCase:
    """Test DeleteClientUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_deletes_client_successfully(self):
        """Test successful client deletion."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True

        use_case = DeleteClientUseCase(mock_repo)

        client_id = EntityId.generate()

        result = await use_case.execute(client_id=client_id.value, created_by="test-user")

        assert result is True
        mock_repo.delete.assert_called_once_with(client_id.value)

    @pytest.mark.asyncio
    async def test_execute_not_found_raises_value_error(self):
        """Test that non-existent client raises ValueError."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False

        use_case = DeleteClientUseCase(mock_repo)

        client_id = uuid4()

        with pytest.raises(ClientNotFoundError, match=f"Client not found: {client_id}"):
            await use_case.execute(client_id=client_id, created_by="test-user")
