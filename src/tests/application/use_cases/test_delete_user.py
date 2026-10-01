"""Tests for DeleteUserUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.user.application.use_cases.delete_user import DeleteUserUseCase
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


class TestDeleteUserUseCase:
    @pytest.mark.asyncio
    async def test_hands_their_work_to_the_calling_admin(self):
        workspace_id = EntityId.generate()
        teammate = _user(UserRole.MEMBER, workspace_id)
        ctx = _admin_context(workspace_id)
        repository = AsyncMock()
        repository.find_by_id.return_value = teammate
        repository.delete_handing_over.return_value = True

        await DeleteUserUseCase(repository).execute(str(teammate.id.value), ctx)

        repository.delete_handing_over.assert_awaited_once_with(teammate.id, successor_id=ctx.user_id)

    @pytest.mark.asyncio
    async def test_unknown_user_is_not_found(self):
        repository = AsyncMock()
        repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await DeleteUserUseCase(repository).execute(
                str(EntityId.generate().value), _admin_context(EntityId.generate())
            )

    @pytest.mark.asyncio
    async def test_user_of_another_workspace_is_not_found(self):
        teammate = _user(UserRole.MEMBER, EntityId.generate())
        repository = AsyncMock()
        repository.find_by_id.return_value = teammate

        with pytest.raises(UserNotFoundError):
            await DeleteUserUseCase(repository).execute(str(teammate.id.value), _admin_context(EntityId.generate()))

        repository.delete_handing_over.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_admin_cannot_be_deleted(self):
        workspace_id = EntityId.generate()
        admin = _user(UserRole.ADMIN, workspace_id)
        repository = AsyncMock()
        repository.find_by_id.return_value = admin

        with pytest.raises(ValueError, match="Admin"):
            await DeleteUserUseCase(repository).execute(str(admin.id.value), _admin_context(workspace_id))

        repository.delete_handing_over.assert_not_awaited()
