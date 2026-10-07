"""Tests for GetUserByIdUseCase: users are visible only within the caller's workspace."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import TEST_WORKSPACE_ID, make_request_context


def build_user(user_id: str, workspace_id: str) -> UserEntity:
    return UserEntity(
        id=EntityId.from_string(user_id),
        email=Email("someone@example.com"),
        display_name="Someone",
        password_hash="hash",
        role=UserRole.MEMBER,
        workspace_id=EntityId.from_string(workspace_id),
    )


def build_use_case(user: UserEntity | None) -> GetUserByIdUseCase:
    user_repository = AsyncMock()
    user_repository.find_by_id.return_value = user
    return GetUserByIdUseCase(user_repository)


class TestGetUserById:
    @pytest.mark.asyncio
    async def test_a_teammate_is_returned(self):
        teammate_id = str(uuid4())
        use_case = build_use_case(build_user(teammate_id, TEST_WORKSPACE_ID))

        result = await use_case.execute(teammate_id, make_request_context())

        assert result.id == teammate_id

    @pytest.mark.asyncio
    async def test_a_user_of_another_workspace_is_not_found(self):
        stranger_id = str(uuid4())
        use_case = build_use_case(build_user(stranger_id, str(uuid4())))

        with pytest.raises(UserNotFoundError):
            await use_case.execute(stranger_id, make_request_context())
