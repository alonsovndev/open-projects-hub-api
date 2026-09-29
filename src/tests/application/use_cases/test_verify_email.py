"""
Tests for VerifyEmailUseCase.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.app.features.auth.application.dtos.auth_dto import VerifyEmailRequest
from src.app.features.auth.application.use_cases.verify_email import VerifyEmailUseCase
from src.app.features.auth.domain.entities.email_verification_code import EmailVerificationCode
from src.app.features.auth.domain.exceptions.auth_exceptions import (
    InvalidVerificationCodeError,
    VerificationRateLimitedError,
)
from src.app.features.user.domain.entities.user_entity import INITIAL_AI_CREDITS, UserEntity
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


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
    return AsyncMock()


async def _make_valid_code(user_entity, plain_code="ABC234"):
    code_hash = await PasswordHandler.hash_password(plain_code)
    return EmailVerificationCode(
        id=EntityId.generate(),
        user_id=user_entity.id,
        code_hash=code_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )


def _request(code="ABC234", email="new@example.com"):
    return VerifyEmailRequest(email=email, code=code)


class TestVerifyEmailUseCase:
    @pytest.mark.asyncio
    async def test_valid_code_verifies_the_account_and_grants_credits(
        self, pending_user, mock_user_repository, mock_verification_code_repository
    ):
        verification_code = await _make_valid_code(pending_user)
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(mock_user_repository, mock_verification_code_repository)
        response = await use_case.execute(_request())

        assert response.verified is True
        assert pending_user.is_email_verified is True
        assert pending_user.ai_credits_remaining == INITIAL_AI_CREDITS
        assert verification_code.used_at is not None
        mock_user_repository.update.assert_awaited_once_with(pending_user)

    @pytest.mark.asyncio
    async def test_code_is_accepted_regardless_of_case_and_whitespace(
        self, pending_user, mock_user_repository, mock_verification_code_repository
    ):
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = await _make_valid_code(
            pending_user
        )

        use_case = VerifyEmailUseCase(mock_user_repository, mock_verification_code_repository)
        response = await use_case.execute(_request(code=" abc234 "))

        assert response.verified is True

    @pytest.mark.asyncio
    async def test_wrong_code_records_a_failed_attempt(
        self, pending_user, mock_user_repository, mock_verification_code_repository
    ):
        verification_code = await _make_valid_code(pending_user)
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(mock_user_repository, mock_verification_code_repository)
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request(code="ZZZ999"))

        assert verification_code.attempt_count == 1
        assert pending_user.is_email_verified is False
        mock_verification_code_repository.save.assert_awaited_once_with(verification_code)
        mock_user_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_expired_or_superseded_code_is_rejected(
        self, mock_user_repository, mock_verification_code_repository
    ):
        # The repository only returns unexpired, unused codes.
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = None

        use_case = VerifyEmailUseCase(mock_user_repository, mock_verification_code_repository)
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request())

    @pytest.mark.asyncio
    async def test_code_is_locked_after_five_failed_attempts(
        self, pending_user, mock_user_repository, mock_verification_code_repository
    ):
        verification_code = await _make_valid_code(pending_user)
        verification_code.attempt_count = EmailVerificationCode.MAX_VALIDATION_ATTEMPTS
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(mock_user_repository, mock_verification_code_repository)
        # Even the right code is refused once locked: a new code must be requested.
        with pytest.raises(VerificationRateLimitedError, match="request a new code"):
            await use_case.execute(_request())

        assert pending_user.is_email_verified is False

    @pytest.mark.asyncio
    async def test_unknown_email_gets_the_same_error_as_a_wrong_code(
        self, mock_user_repository, mock_verification_code_repository
    ):
        mock_user_repository.find_by_email.return_value = None

        use_case = VerifyEmailUseCase(mock_user_repository, mock_verification_code_repository)
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request())

        mock_verification_code_repository.find_latest_active_by_user_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_already_verified_account_gets_the_same_error_as_a_wrong_code(
        self, pending_user, mock_user_repository, mock_verification_code_repository
    ):
        pending_user.verify_email()

        use_case = VerifyEmailUseCase(mock_user_repository, mock_verification_code_repository)
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request())

        mock_user_repository.update.assert_not_awaited()
