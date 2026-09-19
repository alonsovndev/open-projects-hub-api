"""
Tests for ChangePasswordUseCase.

Tests password change with current password verification.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestChangePasswordUseCase:
    """Test ChangePasswordUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_changes_password_successfully(self):
        """Test that execute successfully changes password when current password is correct."""
        mock_repo = AsyncMock()

        user_id = EntityId.generate()
        user_entity = UserEntity(
            id=user_id,
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="old_hashed_password",
            role=UserRole.VIEWER,
        )
        mock_repo.find_by_id.return_value = user_entity
        mock_repo.save.return_value = user_entity

        use_case = ChangePasswordUseCase(mock_repo)

        with (
            patch(
                "src.app.shared.infrastructure.security.password_handler.PasswordHandler.verify_password"
            ) as mock_verify,
            patch("src.app.shared.infrastructure.security.password_handler.PasswordHandler.hash_password") as mock_hash,
        ):
            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"

            await use_case.execute(user_id=str(user_id.value), current_password="OldPass123", new_password="NewPass456")

            mock_verify.assert_called_once_with("OldPass123", "old_hashed_password")
            mock_hash.assert_called_once_with("NewPass456")
            mock_repo.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_incorrect_current_password(self):
        """Test that execute raises ValueError when current password is incorrect."""
        mock_repo = AsyncMock()

        user_id = EntityId.generate()
        user_entity = UserEntity(
            id=user_id,
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        mock_repo.find_by_id.return_value = user_entity

        use_case = ChangePasswordUseCase(mock_repo)

        with patch(
            "src.app.shared.infrastructure.security.password_handler.PasswordHandler.verify_password"
        ) as mock_verify:
            mock_verify.return_value = False

            with pytest.raises(ValueError, match="Current password is incorrect"):
                await use_case.execute(
                    user_id=str(user_id.value), current_password="WrongPass", new_password="NewPass456"
                )

            mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_raises_not_found_for_nonexistent_user(self):
        """Test that execute raises UserNotFoundError when user doesn't exist."""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        use_case = ChangePasswordUseCase(mock_repo)

        user_id = str(EntityId.generate().value)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(user_id=user_id, current_password="OldPass123", new_password="NewPass456")

        mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_validates_new_password_min_length(self):
        """Test that execute validates new password minimum length."""
        mock_repo = AsyncMock()

        user_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        mock_repo.find_by_id.return_value = user_entity

        use_case = ChangePasswordUseCase(mock_repo)

        with patch(
            "src.app.shared.infrastructure.security.password_handler.PasswordHandler.verify_password"
        ) as mock_verify:
            mock_verify.return_value = True

            with pytest.raises(ValueError, match="Password must be at least 8 characters"):
                await use_case.execute(
                    user_id=str(user_entity.id.value), current_password="OldPass123", new_password="Short1"
                )

        mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_validates_new_password_contains_letter(self):
        """Test that execute validates new password contains a letter."""
        mock_repo = AsyncMock()

        user_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        mock_repo.find_by_id.return_value = user_entity

        use_case = ChangePasswordUseCase(mock_repo)

        with patch(
            "src.app.shared.infrastructure.security.password_handler.PasswordHandler.verify_password"
        ) as mock_verify:
            mock_verify.return_value = True

            with pytest.raises(ValueError, match="Password must contain at least one letter"):
                await use_case.execute(
                    user_id=str(user_entity.id.value), current_password="OldPass123", new_password="12345678"
                )

        mock_repo.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_validates_new_password_contains_digit(self):
        """Test that execute validates new password contains a digit."""
        mock_repo = AsyncMock()

        user_entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Test User",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        mock_repo.find_by_id.return_value = user_entity

        use_case = ChangePasswordUseCase(mock_repo)

        with patch(
            "src.app.shared.infrastructure.security.password_handler.PasswordHandler.verify_password"
        ) as mock_verify:
            mock_verify.return_value = True

            with pytest.raises(ValueError, match="Password must contain at least one digit"):
                await use_case.execute(
                    user_id=str(user_entity.id.value), current_password="OldPass123", new_password="NoDigitsHere"
                )

        mock_repo.save.assert_not_awaited()
