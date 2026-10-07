"""Tests for UpdateUserStatusUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.user.application.use_cases.update_user_status import UpdateUserStatusUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


def _user(role: UserRole, workspace_id: EntityId) -> UserEntity:
    return UserEntity(
        id=EntityId.generate(),
        email=Email("teammate@example.com"),
        display_name="Teammate",
        password_hash="hashed_password",
        role=role,
        workspace_id=workspace_id,
    )


def _admin_context(workspace_id: EntityId) -> RequestContext:
    return RequestContext(user_id=EntityId.generate(), workspace_id=workspace_id, role=UserRole.ADMIN)


def _repository_returning(user: UserEntity | None) -> AsyncMock:
    repository = AsyncMock()
    repository.find_by_id.return_value = user
    repository.update.side_effect = lambda saved: saved
    return repository


class TestUpdateUserStatusUseCase:
    @pytest.mark.asyncio
    async def test_deactivating_revokes_sessions(self):
        workspace_id = EntityId.generate()
        teammate = _user(UserRole.MEMBER, workspace_id)

        result = await UpdateUserStatusUseCase(_repository_returning(teammate)).execute(
            str(teammate.id.value), False, _admin_context(workspace_id)
        )

        assert result.is_active is False
        assert teammate.token_version == 1

    @pytest.mark.asyncio
    async def test_activating_keeps_earlier_sessions_revoked(self):
        workspace_id = EntityId.generate()
        teammate = _user(UserRole.MEMBER, workspace_id)
        teammate.deactivate()

        result = await UpdateUserStatusUseCase(_repository_returning(teammate)).execute(
            str(teammate.id.value), True, _admin_context(workspace_id)
        )

        assert result.is_active is True
        assert teammate.token_version == 1

    @pytest.mark.asyncio
    async def test_repeating_the_current_status_saves_nothing(self):
        workspace_id = EntityId.generate()
        teammate = _user(UserRole.MEMBER, workspace_id)
        repository = _repository_returning(teammate)

        await UpdateUserStatusUseCase(repository).execute(str(teammate.id.value), True, _admin_context(workspace_id))

        repository.update.assert_not_awaited()
        assert teammate.token_version == 0

    @pytest.mark.asyncio
    async def test_user_of_another_workspace_is_not_found(self):
        teammate = _user(UserRole.MEMBER, EntityId.generate())

        with pytest.raises(UserNotFoundError):
            await UpdateUserStatusUseCase(_repository_returning(teammate)).execute(
                str(teammate.id.value), False, _admin_context(EntityId.generate())
            )

    @pytest.mark.asyncio
    async def test_admin_cannot_be_deactivated(self):
        workspace_id = EntityId.generate()
        admin = _user(UserRole.ADMIN, workspace_id)

        with pytest.raises(ValueError, match="Admin"):
            await UpdateUserStatusUseCase(_repository_returning(admin)).execute(
                str(admin.id.value), False, _admin_context(workspace_id)
            )
