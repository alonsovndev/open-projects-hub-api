"""Tests for UpdateUserOnboardingUseCase (F-005)."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.user.application.use_cases.update_user_onboarding import UpdateUserOnboardingUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


def build_user() -> UserEntity:
    return UserEntity.create(
        email="admin@example.com",
        display_name="Admin",
        password_hash="hashed",
        role=UserRole.ADMIN,
    )


class TestUpdateUserOnboardingUseCase:
    @pytest.mark.asyncio
    async def test_completed_true_dismisses_onboarding(self):
        user = build_user()
        repository = AsyncMock()
        repository.find_by_id.return_value = user
        repository.update.side_effect = lambda entity: entity

        result = await UpdateUserOnboardingUseCase(repository).execute(str(user.id.value), completed=True)

        assert result.onboarding_completed is True
        repository.update.assert_awaited_once_with(user)

    @pytest.mark.asyncio
    async def test_completed_false_replays_onboarding(self):
        user = build_user()
        user.complete_onboarding()
        repository = AsyncMock()
        repository.find_by_id.return_value = user
        repository.update.side_effect = lambda entity: entity

        result = await UpdateUserOnboardingUseCase(repository).execute(str(user.id.value), completed=False)

        assert result.onboarding_completed is False

    @pytest.mark.asyncio
    async def test_unknown_user_raises_not_found(self):
        repository = AsyncMock()
        repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await UpdateUserOnboardingUseCase(repository).execute(str(EntityId.generate().value), completed=True)

        repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_user_vanishing_before_save_raises_not_found(self):
        user = build_user()
        repository = AsyncMock()
        repository.find_by_id.return_value = user
        repository.update.return_value = None

        with pytest.raises(UserNotFoundError):
            await UpdateUserOnboardingUseCase(repository).execute(str(user.id.value), completed=True)
