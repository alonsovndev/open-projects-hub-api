"""
Tests for UserPreferencesRepositoryImpl.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.value_objects.theme import Theme
from src.app.features.user.infrastructure.models.user_preferences_model import UserPreferencesModel
from src.app.features.user.infrastructure.repositories.user_preferences_repository_impl import (
    UserPreferencesRepositoryImpl,
)
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create repository with mocked session."""
    return UserPreferencesRepositoryImpl(mock_session)


@pytest.fixture
def user_id():
    """Create a test user ID."""
    return EntityId.generate()


@pytest.fixture
def preferences_entity(user_id):
    """Create a test preferences entity."""
    return UserPreferencesEntity(
        id=EntityId.generate(),
        user_id=user_id,
        theme=Theme.DARK,
        language="en",
    )


@pytest.fixture
def preferences_model(user_id):
    """Create a test preferences model."""
    model_id = EntityId.generate()
    return UserPreferencesModel(
        id=model_id.value,
        user_id=user_id.value,
        theme="dark",
        language="en",
    )


class TestFindByUserId:
    """Tests for find_by_user_id method."""

    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_entity_when_found(
        self, repository, mock_session, user_id, preferences_model
    ):
        """Test finding preferences returns entity when found."""
        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = preferences_model
        mock_session.execute.return_value = mock_result

        # Execute
        result = await repository.find_by_user_id(user_id)

        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert result.theme == Theme.DARK
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_none_when_not_found(
        self, repository, mock_session, user_id
    ):
        """Test finding preferences returns None when not found."""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await repository.find_by_user_id(user_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_user_id_raises_exception_on_database_error(
        self, repository, mock_session, user_id
    ):
        """Test find_by_user_id raises exception when database error occurs."""
        # Mock exception
        from sqlalchemy.exc import SQLAlchemyError
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(SQLAlchemyError, match="Database error"):
            await repository.find_by_user_id(user_id)


class TestSave:
    """Tests for save method."""

    @pytest.mark.asyncio
    async def test_save_creates_new_preferences_when_not_exists(
        self, repository, mock_session, preferences_entity
    ):
        """Test save creates new preferences when they don't exist."""
        # Mock: find returns None (not exists)
        mock_find_result = MagicMock()
        mock_find_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_find_result

        # Execute
        result = await repository.save(preferences_entity)

        # Assert
        assert result is not None
        assert result.theme == Theme.DARK
        assert result.language == "en"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_updates_existing_preferences(
        self, repository, mock_session, preferences_entity, preferences_model
    ):
        """Test save updates existing preferences."""
        # Mock: find returns existing model
        mock_find_result = MagicMock()
        mock_find_result.scalar_one_or_none.return_value = preferences_model
        mock_session.execute.return_value = mock_find_result

        # Execute
        result = await repository.save(preferences_entity)

        # Assert
        assert result is not None
        assert result.theme == Theme.DARK
        mock_session.add.assert_not_called()  # Should update, not add
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_raises_exception_on_database_error(
        self, repository, mock_session, preferences_entity
    ):
        """Test save raises exception when database error occurs."""
        # Mock exception during execute
        from sqlalchemy.exc import SQLAlchemyError
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(SQLAlchemyError, match="Database error"):
            await repository.save(preferences_entity)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_raises_exception_on_commit_failure(
        self, repository, mock_session, preferences_entity
    ):
        """Test save raises exception when commit fails."""
        # Mock: find returns None
        from sqlalchemy.exc import SQLAlchemyError
        mock_find_result = MagicMock()
        mock_find_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_find_result
        
        # Mock commit failure
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")

        # Act & Assert
        with pytest.raises(SQLAlchemyError, match="Commit failed"):
            await repository.save(preferences_entity)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()


class TestDeleteByUserId:
    """Tests for delete_by_user_id method."""

    @pytest.mark.asyncio
    async def test_delete_by_user_id_returns_true_when_deleted(
        self, repository, mock_session, user_id
    ):
        """Test delete returns True when preferences were deleted."""
        # Mock delete result with rowcount > 0
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Execute
        result = await repository.delete_by_user_id(user_id)

        # Assert
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_user_id_returns_false_when_not_found(
        self, repository, mock_session, user_id
    ):
        """Test delete returns False when no preferences found."""
        # Mock delete result with rowcount = 0
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        # Execute
        result = await repository.delete_by_user_id(user_id)

        # Assert
        assert result is False
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_user_id_raises_exception_on_database_error(
        self, repository, mock_session, user_id
    ):
        """Test delete raises exception when database error occurs."""
        # Mock exception
        from sqlalchemy.exc import SQLAlchemyError
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(SQLAlchemyError, match="Database error"):
            await repository.delete_by_user_id(user_id)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()
