"""Tests for GetClientsUseCase."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.app.features.clients.application.dtos.client_dto import PaginatedClientsResponse
from src.app.features.clients.application.use_cases.get_clients import GetClientsUseCase
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestGetClientsUseCase:
    """Test GetClientsUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_returns_paginated_clients(self):
        """Test successful retrieval of paginated clients."""
        mock_repo = AsyncMock()

        client1 = ClientEntity(
            id=EntityId.generate(),
            name="Client One",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        client2 = ClientEntity(
            id=EntityId.generate(),
            name="Client Two",
            created_at=datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc),
        )

        mock_repo.find_all.return_value = [client1, client2]
        mock_repo.count.return_value = 10

        use_case = GetClientsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user", offset=0, limit=20)

        assert isinstance(result, PaginatedClientsResponse)
        assert len(result.items) == 2
        assert result.items[0].name == "Client One"
        assert result.items[1].name == "Client Two"
        assert result.total == 10
        assert result.page == 1
        assert result.per_page == 20

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list(self):
        """Test retrieval when no clients exist."""
        mock_repo = AsyncMock()

        mock_repo.find_all.return_value = []
        mock_repo.count.return_value = 0

        use_case = GetClientsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user", offset=0, limit=20)

        assert isinstance(result, PaginatedClientsResponse)
        assert len(result.items) == 0
        assert result.total == 0
        assert result.page == 1
        assert result.per_page == 20

    @pytest.mark.asyncio
    async def test_execute_pagination_calculation(self):
        """Test page number calculation with different offsets."""
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        mock_repo.count.return_value = 50

        use_case = GetClientsUseCase(mock_repo)

        result_page1 = await use_case.execute(user_id="test-user", offset=0, limit=10)
        assert result_page1.page == 1

        result_page2 = await use_case.execute(user_id="test-user", offset=10, limit=10)
        assert result_page2.page == 2

        result_page3 = await use_case.execute(user_id="test-user", offset=20, limit=10)
        assert result_page3.page == 3

    @pytest.mark.asyncio
    async def test_execute_default_parameters(self):
        """Test execution with default offset and limit."""
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        mock_repo.count.return_value = 0

        use_case = GetClientsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user")

        assert result.page == 1
        assert result.per_page == 100
        mock_repo.find_all.assert_called_once_with(skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_execute_with_clients_having_optional_fields(self):
        """Test retrieval of clients with all optional fields populated."""
        mock_repo = AsyncMock()

        client = ClientEntity(
            id=EntityId.generate(),
            name="Full Client",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        client._email = None
        client._phone = None
        client._company = "Test Company"
        client._address = "123 Test St"
        client._notes = "Important"

        mock_repo.find_all.return_value = [client]
        mock_repo.count.return_value = 1

        use_case = GetClientsUseCase(mock_repo)

        result = await use_case.execute(user_id="test-user", offset=0, limit=20)

        assert len(result.items) == 1
        assert result.items[0].company == "Test Company"
        assert result.items[0].address == "123 Test St"
        assert result.items[0].notes == "Important"
