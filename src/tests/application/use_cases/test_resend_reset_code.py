"""
Tests for ResendResetCodeUseCase.
"""

from unittest.mock import AsyncMock

import pytest

from src.app.features.auth.application.dtos.auth_dto import ResendResetCodeRequest
from src.app.features.auth.application.use_cases.issue_reset_code import MAX_REQUESTS_PER_WINDOW
from src.app.features.auth.application.use_cases.resend_reset_code import ResendResetCodeUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import ResetCodeRateLimitedError
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.fixture
def user_entity():
    return UserEntity(
        id=EntityId.generate(),
        email=Email("admin@example.com"),
        display_name="Admin User",
        password_hash="hashed",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def mock_reset_code_repository():
    return AsyncMock()


@pytest.fixture
def mock_email_sender():
    return AsyncMock()


class TestResendResetCodeUseCase:
    @pytest.mark.asyncio
    async def test_resend_within_limit_issues_new_code(
        self, user_entity, mock_user_repository, mock_reset_code_repository, mock_email_sender
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        mock_reset_code_repository.count_created_since.return_value = MAX_REQUESTS_PER_WINDOW - 1
        use_case = ResendResetCodeUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        await use_case.execute(ResendResetCodeRequest(email="admin@example.com"))

        mock_reset_code_repository.invalidate_active_for_user.assert_awaited_once_with(user_entity.id)
        mock_reset_code_repository.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_resend_at_limit_is_rate_limited(
        self, user_entity, mock_user_repository, mock_reset_code_repository, mock_email_sender
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        mock_reset_code_repository.count_created_since.return_value = MAX_REQUESTS_PER_WINDOW
        use_case = ResendResetCodeUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        with pytest.raises(ResetCodeRateLimitedError):
            await use_case.execute(ResendResetCodeRequest(email="admin@example.com"))

        mock_reset_code_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_email_no_ops(self, mock_user_repository, mock_reset_code_repository, mock_email_sender):
        mock_user_repository.find_by_email.return_value = None
        use_case = ResendResetCodeUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        await use_case.execute(ResendResetCodeRequest(email="ghost@example.com"))

        mock_reset_code_repository.create.assert_not_called()
