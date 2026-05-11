"""
Tests for UpdateUserProfileUseCase.

Tests profile update functionality (display_name only).
"""
import pytest
from unittest.mock import AsyncMock

from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestUpdateUserProfileUseCase:
    """Test UpdateUserProfileUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_updates_display_name(self):
        """Test that execute successfully updates display name."""
        mock_repo = AsyncMock()
        
        user_id = EntityId.generate()
        user_entity = UserEntity(
            id=user_id,
            email=Email("user@example.com"),
            display_name="Old Name",
            password_hash="hashed_password",
            role=UserRole.VIEWER
        )
        mock_repo.find_by_id.return_value = user_entity
        
        updated_entity = UserEntity(
            id=user_id,
            email=Email("user@example.com"),
            display_name="New Name",
            password_hash="hashed_password",
            role=UserRole.VIEWER
        )
        mock_repo.save.return_value = updated_entity
        
        use_case = UpdateUserProfileUseCase(mock_repo)
        
        result = await use_case.execute(str(user_id.value), display_name="New Name")
        
        assert isinstance(result, UserResponse)
        assert result.display_name == "New Name"
        assert result.email == "user@example.com"
        
        mock_repo.find_by_id.assert_awaited_once()
        mock_repo.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_raises_not_found_for_nonexistent_user(self):
        """Test that execute raises UserNotFoundException when user doesn't exist."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        
        use_case = UpdateUserProfileUseCase(mock_repo)
        
        user_id = str(EntityId.generate().value)
        
        with pytest.raises(UserNotFoundException):
            await use_case.execute(user_id, display_name="New Name")
        
        mock_repo.find_by_id.assert_awaited_once()
        mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_validates_display_name_length(self):
        """Test that execute validates display name max length."""
        mock_repo = AsyncMock()
        
        user_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Old Name",
            password_hash="hashed_password",
            role=UserRole.VIEWER
        )
        mock_repo.find_by_id.return_value = user_entity
        
        use_case = UpdateUserProfileUseCase(mock_repo)
        
        long_name = "a" * 256  # Max 255 chars
        
        with pytest.raises(ValueError, match="Display name must not exceed 255 characters"):
            await use_case.execute(str(user_entity.id.value), display_name=long_name)
        
        mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_validates_empty_display_name(self):
        """Test that execute validates empty display name."""
        mock_repo = AsyncMock()
        
        user_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Old Name",
            password_hash="hashed_password",
            role=UserRole.VIEWER
        )
        mock_repo.find_by_id.return_value = user_entity
        
        use_case = UpdateUserProfileUseCase(mock_repo)
        
        with pytest.raises(ValueError, match="Display name cannot be empty"):
            await use_case.execute(str(user_entity.id.value), display_name="")
        
        mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_preserves_other_fields(self):
        """Test that execute preserves email, role, and password_hash."""
        mock_repo = AsyncMock()
        
        user_id = EntityId.generate()
        user_entity = UserEntity(
            id=user_id,
            email=Email("admin@example.com"),
            display_name="Admin User",
            password_hash="original_hash",
            role=UserRole.ADMIN
        )
        mock_repo.find_by_id.return_value = user_entity
        
        # Capture the saved entity
        saved_entity = None
        async def capture_save(entity):
            nonlocal saved_entity
            saved_entity = entity
            return entity
        
        mock_repo.save.side_effect = capture_save
        
        use_case = UpdateUserProfileUseCase(mock_repo)
        
        await use_case.execute(str(user_id.value), display_name="Updated Admin")
        
        # Verify saved entity preserves original fields
        assert saved_entity.email.value == "admin@example.com"
        assert saved_entity.role == UserRole.ADMIN
        assert saved_entity.password_hash == "original_hash"
        assert saved_entity.display_name == "Updated Admin"
