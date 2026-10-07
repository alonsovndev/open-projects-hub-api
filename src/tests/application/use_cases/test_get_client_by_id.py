"""Tests for GetClientByIdUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.clients.application.dtos.client_dto import ClientResponse
from src.app.features.clients.application.use_cases.get_client_by_id import GetClientByIdUseCase
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.domain.exceptions.client_exceptions import ClientNotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


class TestGetClientByIdUseCase:
    """Test GetClientByIdUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_returns_existing_client(self):
        """Test successful retrieval of existing client."""
        mock_repo = AsyncMock()

        client_id = EntityId.generate()
        client = ClientEntity(
            id=client_id,
            name="Test Client",
            company="Test Company",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC),
        )

        mock_repo.find_by_id.return_value = client

        use_case = GetClientByIdUseCase(mock_repo)

        result = await use_case.execute(client_id=client_id.value, ctx=make_request_context())

        assert isinstance(result, ClientResponse)
        assert result.name == "Test Client"
        assert result.company == "Test Company"
        assert result.id == str(client_id.value)

    @pytest.mark.asyncio
    async def test_execute_not_found_raises_value_error(self):
        """Test that non-existent client raises ValueError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = GetClientByIdUseCase(mock_repo)

        client_id = uuid4()

        with pytest.raises(ClientNotFoundError, match=f"Client not found: {client_id}"):
            await use_case.execute(client_id=client_id, ctx=make_request_context())

    @pytest.mark.asyncio
    async def test_execute_returns_client_with_email(self):
        """Test retrieval of client with email."""
        mock_repo = AsyncMock()

        client_id = EntityId.generate()
        client = ClientEntity(
            id=client_id,
            name="Client With Email",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC),
        )
        client._email = None

        mock_repo.find_by_id.return_value = client

        use_case = GetClientByIdUseCase(mock_repo)

        result = await use_case.execute(client_id=client_id.value, ctx=make_request_context())

        assert result.name == "Client With Email"
