"""
Tests for GetUserPreferencesUseCase.
"""

from unittest.mock import AsyncMock

import pytest

from src.app.features.user.application.use_cases.get_user_preferences import GetUserPreferencesUseCase
from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.value_objects.theme import Theme
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture
def mock_repository():
    """Create a mock preferences repository."""
    repository = AsyncMock()
    return repository


@pytest.fixture
def use_case(mock_repository):
    """Create use case with mocked repository."""
    return GetUserPreferencesUseCase(mock_repository)


@pytest.fixture
def user_id():
    """Create a test user ID."""
    return EntityId.generate()


@pytest.fixture
def existing_preferences(user_id):
    """Create existing preferences entity."""
    return UserPreferencesEntity(
        id=EntityId.generate(),
        user_id=user_id,
        theme=Theme.DARK,
        language="es",
    )


class TestGetUserPreferences:
    """Tests for GetUserPreferencesUseCase."""

    @pytest.mark.asyncio
    async def test_returns_existing_preferences_when_found(
        self, use_case, mock_repository, user_id, existing_preferences
    ):
        """Test returns existing preferences when they exist."""
        # Mock repository to return existing preferences
        mock_repository.find_by_user_id.return_value = existing_preferences

        # Execute
        result = await use_case.execute(user_id)

        # Assert
        assert result == existing_preferences
        assert result.theme == Theme.DARK
        assert result.language == "es"
        mock_repository.find_by_user_id.assert_called_once_with(user_id)
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_and_saves_default_when_not_found(self, use_case, mock_repository, user_id):
        """Test creates and persists default preferences when none exist."""
        # Mock repository to return None (not found)
        mock_repository.find_by_user_id.return_value = None

        # Mock save to return the saved entity
        def save_side_effect(entity):
            return entity

        mock_repository.save.side_effect = save_side_effect

        # Execute
        result = await use_case.execute(user_id)

        # Assert - verify default values
        assert result is not None
        assert result.user_id == user_id
        assert result.theme == Theme.AUTO
        assert result.language == "en"

        mock_repository.find_by_user_id.assert_called_once_with(user_id)
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_default_when_save_fails(self, use_case, mock_repository, user_id):
        """Test returns in-memory default when save fails."""
        # Mock repository to return None (not found)
        mock_repository.find_by_user_id.return_value = None

        # Mock save to return None (failure)
        mock_repository.save.return_value = None

        # Execute
        result = await use_case.execute(user_id)

        # Assert - should still return default even if save failed
        assert result is not None
        assert result.user_id == user_id
        assert result.theme == Theme.AUTO
        assert result.language == "en"

        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_default_preferences_have_correct_structure(self, use_case, mock_repository, user_id):
        """Test default preferences match API spec requirements."""
        # Mock repository to return None
        mock_repository.find_by_user_id.return_value = None
        mock_repository.save.side_effect = lambda entity: entity

        # Execute
        result = await use_case.execute(user_id)

        # Assert all required fields per API spec
        assert hasattr(result, "id")
        assert hasattr(result, "user_id")
        assert hasattr(result, "theme")
        assert hasattr(result, "language")
