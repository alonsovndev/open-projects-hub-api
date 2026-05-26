"""
Tests for GetUserProfileUseCase.

Tests profile retrieval for authenticated users.
"""

from unittest.mock import AsyncMock

import pytest

from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestGetUserProfileUseCase:
    """Test GetUserProfileUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_returns_user_profile(self):
        """Test that execute returns user profile for valid user_id."""
        mock_repo = AsyncMock()

        user_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        mock_repo.find_by_id.return_value = user_entity

        use_case = GetUserProfileUseCase(mock_repo)

        result = await use_case.execute(str(user_entity.id.value))

        assert isinstance(result, UserResponse)
        assert result.id == str(user_entity.id.value)
        assert result.email == "user@example.com"
        assert result.display_name == "Test User"
        assert result.role == "viewer"

        mock_repo.find_by_id.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_raises_not_found_for_nonexistent_user(self):
        """Test that execute raises UserNotFoundException when user doesn't exist."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = GetUserProfileUseCase(mock_repo)

        nonexistent_id = str(EntityId.generate().value)

        with pytest.raises(UserNotFoundException):
            await use_case.execute(nonexistent_id)

        mock_repo.find_by_id.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_with_admin_role(self):
        """Test that execute correctly handles admin role."""
        mock_repo = AsyncMock()

        user_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("admin@example.com"),
            display_name="Admin User",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
        )
        mock_repo.find_by_id.return_value = user_entity

        use_case = GetUserProfileUseCase(mock_repo)

        result = await use_case.execute(str(user_entity.id.value))

        assert result.role == "admin"
