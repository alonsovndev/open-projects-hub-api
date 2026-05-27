"""
Tests for UpdateUserPreferencesUseCase.
"""

from unittest.mock import AsyncMock

import pytest

from src.app.features.user.application.use_cases.update_user_preferences import UpdateUserPreferencesUseCase
from src.app.features.user.domain.entities.user_preferences_entity import UserPreferencesEntity
from src.app.features.user.domain.value_objects.theme import Theme
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture
def mock_repository():
    """Create a mock preferences repository."""
    return AsyncMock()


@pytest.fixture
def use_case(mock_repository):
    """Create use case with mocked repository."""
    return UpdateUserPreferencesUseCase(mock_repository)


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
        theme=Theme.AUTO,
        language="en",
    )


class TestUpdateUserPreferences:
    """Tests for UpdateUserPreferencesUseCase."""

    @pytest.mark.asyncio
    async def test_update_theme_only(self, use_case, mock_repository, user_id, existing_preferences):
        """Test updating only theme preference."""
        # Mock repository
        mock_repository.find_by_user_id.return_value = existing_preferences
        mock_repository.save.side_effect = lambda entity: entity

        # Execute - update theme only
        result = await use_case.execute(user_id, theme=Theme.DARK)

        # Assert
        assert result is not None
        assert result.theme == Theme.DARK
        assert result.language == "en"  # unchanged

        mock_repository.find_by_user_id.assert_called_once_with(user_id)
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_language_only(self, use_case, mock_repository, user_id, existing_preferences):
        """Test updating only language preference."""
        # Mock repository
        mock_repository.find_by_user_id.return_value = existing_preferences
        mock_repository.save.side_effect = lambda entity: entity

        # Execute - update language only
        result = await use_case.execute(user_id, language="es")

        # Assert
        assert result is not None
        assert result.theme == Theme.AUTO  # unchanged
        assert result.language == "es"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, use_case, mock_repository, user_id, existing_preferences):
        """Test updating multiple fields at once."""
        # Mock repository
        mock_repository.find_by_user_id.return_value = existing_preferences
        mock_repository.save.side_effect = lambda entity: entity

        # Execute - update multiple fields
        result = await use_case.execute(user_id, theme=Theme.LIGHT, language="fr")

        # Assert
        assert result is not None
        assert result.theme == Theme.LIGHT
        assert result.language == "fr"

    @pytest.mark.asyncio
    async def test_creates_defaults_when_preferences_not_found(self, use_case, mock_repository, user_id):
        """Test creates default preferences when none exist, then applies update."""
        # Mock repository to return None (no existing preferences)
        mock_repository.find_by_user_id.return_value = None
        mock_repository.save.side_effect = lambda entity: entity

        # Execute - should create defaults then apply update
        result = await use_case.execute(user_id, theme=Theme.DARK)

        # Assert defaults were created with update applied
        assert result is not None
        assert result.theme == Theme.DARK  # update applied
        assert result.language == "en"  # default
        assert result.user_id == user_id

        # Save should have been called once with created entity
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_save_fails(self, use_case, mock_repository, user_id, existing_preferences):
        """Test returns None when save operation fails."""
        # Mock repository
        mock_repository.find_by_user_id.return_value = existing_preferences
        mock_repository.save.return_value = None  # Save failure

        # Execute
        result = await use_case.execute(user_id, theme=Theme.DARK)

        # Assert
        assert result is None
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_update_when_no_fields_provided(self, use_case, mock_repository, user_id, existing_preferences):
        """Test behavior when no fields are provided for update."""
        # Mock repository
        mock_repository.find_by_user_id.return_value = existing_preferences
        mock_repository.save.side_effect = lambda entity: entity

        # Execute - no fields provided
        result = await use_case.execute(user_id)

        # Assert - preferences returned unchanged
        assert result is not None
        assert result.theme == Theme.AUTO
        assert result.language == "en"

        # Save should still be called (even though nothing changed)
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_defaults_when_no_fields_provided(self, use_case, mock_repository, user_id):
        """Test creates default preferences when none exist and no fields provided."""
        # Mock repository to return None
        mock_repository.find_by_user_id.return_value = None
        mock_repository.save.side_effect = lambda entity: entity

        # Execute - no fields provided, no existing preferences
        result = await use_case.execute(user_id)

        # Assert - default preferences created
        assert result is not None
        assert result.theme == Theme.AUTO
        assert result.language == "en"
        assert result.user_id == user_id

        mock_repository.save.assert_called_once()
