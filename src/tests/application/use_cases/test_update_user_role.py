"""Tests for UpdateUserRoleUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.user.application.dtos.user_dto import UpdateUserRoleRequest
from src.app.features.user.application.use_cases.update_user_role import UpdateUserRoleUseCase
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


class TestUpdateUserRoleUseCase:
    @pytest.mark.asyncio
    async def test_changes_role_and_revokes_sessions(self):
        workspace_id = EntityId.generate()
        teammate = _user(UserRole.MEMBER, workspace_id)
        repository = AsyncMock()
        repository.find_by_id.return_value = teammate
        repository.update.side_effect = lambda user: user

        result = await UpdateUserRoleUseCase(repository).execute(
            str(teammate.id.value), "viewer", _admin_context(workspace_id)
        )

        assert result.role == "viewer"
        assert teammate.token_version == 1
        repository.update.assert_awaited_once_with(teammate)

    @pytest.mark.asyncio
    async def test_unknown_user_is_not_found(self):
        repository = AsyncMock()
        repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await UpdateUserRoleUseCase(repository).execute(
                str(EntityId.generate().value), "viewer", _admin_context(EntityId.generate())
            )

    @pytest.mark.asyncio
    async def test_user_of_another_workspace_is_not_found(self):
        teammate = _user(UserRole.MEMBER, EntityId.generate())
        repository = AsyncMock()
        repository.find_by_id.return_value = teammate

        with pytest.raises(UserNotFoundError):
            await UpdateUserRoleUseCase(repository).execute(
                str(teammate.id.value), "viewer", _admin_context(EntityId.generate())
            )

        repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_admin_role_cannot_be_changed(self):
        workspace_id = EntityId.generate()
        admin = _user(UserRole.ADMIN, workspace_id)
        repository = AsyncMock()
        repository.find_by_id.return_value = admin

        with pytest.raises(ValueError, match="Admin"):
            await UpdateUserRoleUseCase(repository).execute(str(admin.id.value), "viewer", _admin_context(workspace_id))

        repository.update.assert_not_awaited()


class TestUpdateUserRoleRequest:
    def test_normalizes_role(self):
        assert UpdateUserRoleRequest(role=" Viewer ").role == "viewer"

    def test_rejects_admin(self):
        with pytest.raises(ValueError, match="member, viewer"):
            UpdateUserRoleRequest(role="admin")
