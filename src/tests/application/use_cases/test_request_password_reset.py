"""
Tests for RequestPasswordResetUseCase.
"""

from unittest.mock import AsyncMock

import pytest

from src.app.features.auth.application.dtos.auth_dto import ForgotPasswordRequest
from src.app.features.auth.application.use_cases.issue_reset_code import GENERIC_RESET_MESSAGE
from src.app.features.auth.application.use_cases.request_password_reset import RequestPasswordResetUseCase
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
    repository = AsyncMock()
    # Default to "no codes issued in this window" so only the rate-limit tests
    # exercise that branch; an unset AsyncMock would compare truthy against the cap.
    repository.count_created_since.return_value = 0
    return repository


@pytest.fixture
def mock_email_sender():
    return AsyncMock()


class TestRequestPasswordResetUseCase:
    @pytest.mark.asyncio
    async def test_known_email_issues_and_emails_a_code(
        self, user_entity, mock_user_repository, mock_reset_code_repository, mock_email_sender
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        use_case = RequestPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        response = await use_case.execute(ForgotPasswordRequest(email="admin@example.com"))

        assert response.message == GENERIC_RESET_MESSAGE
        mock_reset_code_repository.invalidate_active_for_user.assert_awaited_once_with(user_entity.id)
        mock_reset_code_repository.create.assert_awaited_once()
        mock_email_sender.send.assert_awaited_once()
        assert mock_email_sender.send.call_args.kwargs["to"] == "admin@example.com"

    @pytest.mark.asyncio
    async def test_unknown_email_returns_same_generic_message_without_side_effects(
        self, mock_user_repository, mock_reset_code_repository, mock_email_sender
    ):
        """Non-enumeration: unknown emails get the identical response with no code issued (FR-009-01)."""
        mock_user_repository.find_by_email.return_value = None
        use_case = RequestPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        response = await use_case.execute(ForgotPasswordRequest(email="ghost@example.com"))

        assert response.message == GENERIC_RESET_MESSAGE
        mock_reset_code_repository.create.assert_not_called()
        mock_email_sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_at_window_cap_issues_no_further_code(
        self, user_entity, mock_user_repository, mock_reset_code_repository, mock_email_sender
    ):
        """NFR-009-02 caps code requests per email, not per endpoint — this path counts too."""
        mock_user_repository.find_by_email.return_value = user_entity
        mock_reset_code_repository.count_created_since.return_value = 3
        use_case = RequestPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        response = await use_case.execute(ForgotPasswordRequest(email="admin@example.com"))

        assert response.message == GENERIC_RESET_MESSAGE
        mock_reset_code_repository.create.assert_not_called()
        mock_email_sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_below_window_cap_still_issues_a_code(
        self, user_entity, mock_user_repository, mock_reset_code_repository, mock_email_sender
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        mock_reset_code_repository.count_created_since.return_value = 2
        use_case = RequestPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        await use_case.execute(ForgotPasswordRequest(email="admin@example.com"))

        mock_reset_code_repository.create.assert_awaited_once()
        mock_email_sender.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_email_delivery_failure_still_returns_generic_success(
        self, user_entity, mock_user_repository, mock_reset_code_repository, mock_email_sender
    ):
        """A delivery failure must not surface as a different response (would leak account existence)."""
        mock_user_repository.find_by_email.return_value = user_entity
        mock_email_sender.send.side_effect = Exception("smtp down")
        use_case = RequestPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, mock_email_sender)

        response = await use_case.execute(ForgotPasswordRequest(email="admin@example.com"))

        assert response.message == GENERIC_RESET_MESSAGE
