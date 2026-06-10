"""Tests for CreateClientUseCase."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.app.features.clients.application.dtos.client_dto import ClientResponse, CreateClientRequest
from src.app.features.clients.application.use_cases.create_client import CreateClientUseCase
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestCreateClientUseCase:
    """Test CreateClientUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_creates_client_successfully(self):
        """Test successful client creation with minimal fields."""
        mock_repo = AsyncMock()

        created_entity = ClientEntity(
            id=EntityId.generate(),
            name="New Client",
            email=None,
            phone=None,
            company=None,
            address=None,
            notes=None,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.save.return_value = created_entity

        use_case = CreateClientUseCase(mock_repo)

        request = CreateClientRequest(name="New Client")

        result = await use_case.execute(request=request, created_by="test-user")

        assert isinstance(result, ClientResponse)
        assert result.name == "New Client"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_creates_client_with_all_fields(self):
        """Test client creation with all optional fields."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None

        created_entity = ClientEntity(
            id=EntityId.generate(),
            name="Full Client",
            email=None,
            phone=None,
            company="Test Company",
            address="123 Test St",
            notes="Important client",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        created_entity._email = None
        created_entity._phone = None
        mock_repo.save.return_value = created_entity

        use_case = CreateClientUseCase(mock_repo)

        request = CreateClientRequest(
            name="Full Client",
            email="test@example.com",
            phone="+1234567890",
            company="Test Company",
            address="123 Test St",
            notes="Important client",
        )

        result = await use_case.execute(request=request, created_by="test-user")

        assert isinstance(result, ClientResponse)
        assert result.name == "Full Client"
        assert result.company == "Test Company"
        assert result.address == "123 Test St"
        assert result.notes == "Important client"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_email_uniqueness_constraint(self):
        """Test that duplicate email raises ValueError."""
        mock_repo = AsyncMock()

        existing_client = AsyncMock()
        mock_repo.find_by_email.return_value = existing_client

        use_case = CreateClientUseCase(mock_repo)

        request = CreateClientRequest(
            name="New Client",
            email="duplicate@example.com",
        )

        with pytest.raises(ValueError, match=r"Client with email duplicate@example.com already exists"):
            await use_case.execute(request=request, created_by="test-user")

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_empty_name(self):
        """Test that empty name raises ValidationError at DTO level."""
        mock_repo = AsyncMock()

        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Client name cannot be empty"):
            CreateClientRequest(name="")

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_name_too_long(self):
        """Test that name > 200 chars raises ValidationError at DTO level."""
        mock_repo = AsyncMock()

        from pydantic import ValidationError

        long_name = "a" * 201

        with pytest.raises(ValidationError, match="Client name cannot exceed 200 characters"):
            CreateClientRequest(name=long_name)

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_on_company_too_long(self):
        """Test that company > 200 chars raises ValidationError at DTO level."""
        mock_repo = AsyncMock()

        from pydantic import ValidationError

        long_company = "a" * 201

        with pytest.raises(ValidationError, match="Company name cannot exceed 200 characters"):
            CreateClientRequest(name="Test Client", company=long_company)

        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_save_fails(self):
        """Test that save failure raises AttributeError."""
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        mock_repo.save.return_value = None

        use_case = CreateClientUseCase(mock_repo)

        request = CreateClientRequest(name="Test Client")

        with pytest.raises(AttributeError):
            await use_case.execute(request=request, created_by="test-user")

        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_no_email_check_when_email_is_none(self):
        """Test that email uniqueness is not checked when email is None."""
        mock_repo = AsyncMock()

        created_entity = ClientEntity(
            id=EntityId.generate(),
            name="Client Without Email",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        mock_repo.save.return_value = created_entity

        use_case = CreateClientUseCase(mock_repo)

        request = CreateClientRequest(name="Client Without Email")

        result = await use_case.execute(request=request, created_by="test-user")

        assert result.name == "Client Without Email"
        mock_repo.find_by_email.assert_not_called()
        mock_repo.save.assert_called_once()
