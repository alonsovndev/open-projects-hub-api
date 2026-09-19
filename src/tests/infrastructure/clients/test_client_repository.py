"""Unit tests for ClientRepositoryImpl.

Regression coverage for a bug where save/update/delete only called `flush()`
and never `commit()` — writes looked successful (the row was visible within
the same session) but were silently discarded once the session closed,
because nothing ever committed the transaction.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.infrastructure.models.client_model import ClientModel
from src.app.features.clients.infrastructure.repositories.client_repository_impl import ClientRepositoryImpl
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture
def mock_session():
    """spec=AsyncSession so sync methods (add, delete) aren't auto-mocked as async."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session):
    return ClientRepositoryImpl(mock_session)


@pytest.fixture
def sample_client_entity():
    return ClientEntity.create(name="Test Client", email="client@example.com")


@pytest.fixture
def sample_client_model():
    return ClientModel(
        id=EntityId.generate().value,
        name="Test Client",
        email="client@example.com",
        phone=None,
        company=None,
        address=None,
        notes=None,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


class TestSave:
    @pytest.mark.asyncio
    async def test_save_commits_the_transaction(self, repository, mock_session, sample_client_entity):
        await repository.save(sample_client_entity)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()
        mock_session.flush.assert_not_called()


class TestUpdate:
    @pytest.mark.asyncio
    async def test_update_commits_the_transaction(self, repository, mock_session, sample_client_model):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_client_model
        mock_session.execute.return_value = mock_result

        entity = ClientEntity(
            id=EntityId.from_string(str(sample_client_model.id)),
            name="Updated Name",
        )

        await repository.update(entity)

        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()
        mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_raises_when_client_not_found(self, repository, mock_session):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        entity = ClientEntity(id=EntityId.generate(), name="Ghost")

        with pytest.raises(ValueError, match="Client not found"):
            await repository.update(entity)

        mock_session.commit.assert_not_called()


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_commits_the_transaction(self, repository, mock_session, sample_client_model):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_client_model
        mock_session.execute.return_value = mock_result

        deleted = await repository.delete(sample_client_model.id)

        assert deleted is True
        mock_session.delete.assert_awaited_once_with(sample_client_model)
        mock_session.commit.assert_awaited_once()
        mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, repository, mock_session):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        deleted = await repository.delete(EntityId.generate().value)

        assert deleted is False
        mock_session.commit.assert_not_called()
