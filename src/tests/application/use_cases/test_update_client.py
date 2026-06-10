"""Tests for UpdateClientUseCase."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.clients.application.dtos.client_dto import ClientResponse, UpdateClientRequest
from src.app.features.clients.application.use_cases.update_client import UpdateClientUseCase
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestUpdateClientUseCase:
    """Test UpdateClientUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_updates_client_successfully(self):
        """Test successful client update."""
        mock_repo = AsyncMock()

        client_id = EntityId.generate()
        existing_client = ClientEntity(
            id=client_id,
            name="Old Name",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        updated_client = ClientEntity(
            id=client_id,
            name="New Name",
            company="New Company",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc),
        )

        mock_repo.find_by_id.return_value = existing_client
        mock_repo.update.return_value = updated_client

        use_case = UpdateClientUseCase(mock_repo)

        request = UpdateClientRequest(name="New Name", company="New Company")

        result = await use_case.execute(client_id=client_id.value, request=request, created_by="test-user")

        assert isinstance(result, ClientResponse)
        assert result.name == "New Name"
        assert result.company == "New Company"
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_email_uniqueness_when_changing_email(self):
        """Test that duplicate email raises ValueError when changing email."""
        mock_repo = AsyncMock()

        client_id = EntityId.generate()
        existing_client = ClientEntity(
            id=client_id,
            name="Test Client",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        existing_client._email = Email("old@example.com")

        mock_repo.find_by_id.return_value = existing_client

        duplicate_client = AsyncMock()
        mock_repo.find_by_email.return_value = duplicate_client

        use_case = UpdateClientUseCase(mock_repo)

        request = UpdateClientRequest(email="duplicate@example.com")

        with pytest.raises(ValueError, match=r"Client with email duplicate@example.com already exists"):
            await use_case.execute(client_id=client_id.value, request=request, created_by="test-user")

        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_not_found_raises_value_error(self):
        """Test that non-existent client raises ValueError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = UpdateClientUseCase(mock_repo)

        client_id = uuid4()
        request = UpdateClientRequest(name="New Name")

        with pytest.raises(ValueError, match=f"Client not found: {client_id}"):
            await use_case.execute(client_id=client_id, request=request, created_by="test-user")

    @pytest.mark.asyncio
    async def test_execute_same_email_does_not_check_uniqueness(self):
        """Test that keeping the same email does not trigger uniqueness check."""
        mock_repo = AsyncMock()

        client_id = EntityId.generate()
        existing_client = ClientEntity(
            id=client_id,
            name="Test Client",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        existing_client._email = Email("same@example.com")

        updated_client = ClientEntity(
            id=client_id,
            name="Updated Name",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc),
        )
        updated_client._email = Email("same@example.com")

        mock_repo.find_by_id.return_value = existing_client
        mock_repo.update.return_value = updated_client

        use_case = UpdateClientUseCase(mock_repo)

        request = UpdateClientRequest(name="Updated Name")

        result = await use_case.execute(client_id=client_id.value, request=request, created_by="test-user")

        assert result.name == "Updated Name"
        mock_repo.find_by_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_partial_update(self):
        """Test partial update preserves unchanged fields."""
        mock_repo = AsyncMock()

        client_id = EntityId.generate()
        existing_client = ClientEntity(
            id=client_id,
            name="Test Client",
            company="Original Company",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        updated_client = ClientEntity(
            id=client_id,
            name="Test Client",
            company="Original Company",
            created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc),
        )

        mock_repo.find_by_id.return_value = existing_client
        mock_repo.update.return_value = updated_client

        use_case = UpdateClientUseCase(mock_repo)

        request = UpdateClientRequest()

        result = await use_case.execute(client_id=client_id.value, request=request, created_by="test-user")

        assert result.name == "Test Client"
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_name(self):
        """Test that empty name raises ValidationError at DTO level."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Client name cannot be empty"):
            UpdateClientRequest(name="")
