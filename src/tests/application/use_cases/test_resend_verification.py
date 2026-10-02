"""
Tests for ResendVerificationUseCase.
"""

from unittest.mock import AsyncMock

import pytest

from src.app.features.auth.application.dtos.auth_dto import ResendVerificationRequest
from src.app.features.auth.application.services.email_links import EmailLinks
from src.app.features.auth.application.use_cases.issue_verification_code import (
    GENERIC_RESEND_MESSAGE,
    MAX_CODES_PER_WINDOW,
)
from src.app.features.auth.application.use_cases.resend_verification import ResendVerificationUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import VerificationRateLimitedError
from src.app.features.user.domain.entities.user_entity import UserEntity


@pytest.fixture
def pending_user():
    return UserEntity.create_pending_verification(
        email="new@example.com", display_name="New User", password_hash="hash"
    )


@pytest.fixture
def mock_user_repository(pending_user):
    user_repository = AsyncMock()
    user_repository.find_by_email.return_value = pending_user
    return user_repository


@pytest.fixture
def mock_verification_code_repository():
    verification_code_repository = AsyncMock()
    verification_code_repository.count_created_since.return_value = 1  # the code sent at registration
    return verification_code_repository


@pytest.fixture
def mock_email_sender():
    return AsyncMock()


@pytest.fixture
def use_case(mock_user_repository, mock_verification_code_repository, mock_email_sender):
    return ResendVerificationUseCase(
        mock_user_repository, mock_verification_code_repository, mock_email_sender, EmailLinks("http://localhost:5173")
    )


class TestResendVerificationUseCase:
    @pytest.mark.asyncio
    async def test_resend_supersedes_the_old_code_and_emails_a_new_one(
        self, use_case, pending_user, mock_verification_code_repository, mock_email_sender
    ):
        response = await use_case.execute(ResendVerificationRequest(email="new@example.com"))

        assert response.message == GENERIC_RESEND_MESSAGE
        mock_verification_code_repository.invalidate_active_for_user.assert_awaited_once_with(pending_user.id)
        mock_verification_code_repository.create.assert_awaited_once()
        assert mock_email_sender.send.call_args.kwargs["to"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_three_resends_are_allowed_after_the_registration_code(
        self, use_case, mock_verification_code_repository, mock_email_sender
    ):
        mock_verification_code_repository.count_created_since.return_value = MAX_CODES_PER_WINDOW - 1

        await use_case.execute(ResendVerificationRequest(email="new@example.com"))

        mock_email_sender.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_a_fourth_resend_within_the_window_is_refused(
        self, use_case, mock_verification_code_repository, mock_email_sender
    ):
        assert MAX_CODES_PER_WINDOW == 4  # 1 at registration + 3 resends (FR-008-05)
        mock_verification_code_repository.count_created_since.return_value = MAX_CODES_PER_WINDOW

        with pytest.raises(VerificationRateLimitedError):
            await use_case.execute(ResendVerificationRequest(email="new@example.com"))

        mock_verification_code_repository.create.assert_not_awaited()
        mock_email_sender.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unknown_email_gets_the_generic_response_without_an_email(
        self, use_case, mock_user_repository, mock_email_sender
    ):
        mock_user_repository.find_by_email.return_value = None

        response = await use_case.execute(ResendVerificationRequest(email="nobody@example.com"))

        assert response.message == GENERIC_RESEND_MESSAGE
        mock_email_sender.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_already_verified_account_gets_the_generic_response_without_an_email(
        self, use_case, pending_user, mock_email_sender
    ):
        pending_user.verify_email()

        response = await use_case.execute(ResendVerificationRequest(email="new@example.com"))

        assert response.message == GENERIC_RESEND_MESSAGE
        mock_email_sender.send.assert_not_awaited()
