"""
Tests for RevokeAllUserTokensUseCase.
"""

from unittest.mock import AsyncMock

import pytest

from src.app.features.auth.application.use_cases.revoke_all_user_tokens import RevokeAllUserTokensUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def user_entity():
    return UserEntity(
        id=EntityId.generate(),
        email=Email("test@example.com"),
        display_name="Test User",
        password_hash="hashed",
        role=UserRole.ADMIN,
        token_version=3,
    )


class TestRevokeAllUserTokensUseCase:
    @pytest.mark.asyncio
    async def test_bumps_token_version_and_persists(self, mock_user_repository, user_entity):
        mock_user_repository.find_by_id = AsyncMock(return_value=user_entity)
        use_case = RevokeAllUserTokensUseCase(mock_user_repository)

        await use_case.execute(user_entity.id)

        assert user_entity.token_version == 4
        mock_user_repository.update.assert_awaited_once_with(user_entity)

    @pytest.mark.asyncio
    async def test_noop_for_unknown_user(self, mock_user_repository):
        mock_user_repository.find_by_id = AsyncMock(return_value=None)
        use_case = RevokeAllUserTokensUseCase(mock_user_repository)

        await use_case.execute(EntityId.generate())

        mock_user_repository.update.assert_not_called()
