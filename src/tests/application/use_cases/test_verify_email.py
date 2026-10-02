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
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.workspaces.domain.value_objects.workspace_limits import WorkspaceLimits
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


LIMITS = WorkspaceLimits(max_users=5, ai_credits_ceiling=25, credits_per_user=INITIAL_AI_CREDITS)


@pytest.fixture
def pending_user():
    return UserEntity.create_pending_verification(
        email="new@example.com",
        display_name="New User",
        password_hash="hash",
        role=UserRole.ADMIN,
        workspace_id=EntityId.generate(),
    )


@pytest.fixture
def mock_user_repository(pending_user):
    user_repository = AsyncMock()
    user_repository.find_by_email.return_value = pending_user
    return user_repository


@pytest.fixture
def mock_verification_code_repository():
    return AsyncMock()


@pytest.fixture
def mock_workspace_repository():
    workspace_repository = AsyncMock()
    workspace_repository.reserve_ai_credits.return_value = LIMITS.credits_per_user
    return workspace_repository


async def _make_valid_code(user_entity, plain_code="ABC234"):
    code_hash = await PasswordHandler.hash_password(plain_code)
    return EmailVerificationCode(
        id=EntityId.generate(),
        user_id=user_entity.id,
        code_hash=code_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )


def _invitee(role: UserRole) -> UserEntity:
    return UserEntity.create_workspace_member(
        email="new@example.com",
        display_name="Invitee",
        password_hash="placeholder",
        role=role,
        workspace_id=EntityId.generate(),
    )


def _request(code="ABC234", email="new@example.com"):
    return VerifyEmailRequest(email=email, code=code)


class TestVerifyEmailUseCase:
    @pytest.mark.asyncio
    async def test_valid_code_verifies_the_account_and_grants_credits(
        self, pending_user, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        verification_code = await _make_valid_code(pending_user)
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        response = await use_case.execute(_request())

        assert response.verified is True
        assert pending_user.is_email_verified is True
        assert pending_user.ai_credits_remaining == INITIAL_AI_CREDITS
        assert verification_code.used_at is not None
        mock_user_repository.update.assert_awaited_once_with(pending_user)
        mock_workspace_repository.reserve_ai_credits.assert_awaited_once_with(
            pending_user.workspace_id, LIMITS.credits_per_user, LIMITS.ai_credits_ceiling
        )

    @pytest.mark.asyncio
    async def test_a_verified_member_is_granted_credits(
        self, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        member = _invitee(UserRole.MEMBER)
        mock_user_repository.find_by_email.return_value = member
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = await _make_valid_code(member)

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        await use_case.execute(VerifyEmailRequest(email="new@example.com", code="ABC234", password="MyOwnPass123"))

        assert member.ai_credits_remaining == INITIAL_AI_CREDITS
        assert member.ai_credits_granted == INITIAL_AI_CREDITS

    @pytest.mark.asyncio
    async def test_a_verified_viewer_gets_no_credits_and_reserves_none(
        self, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        viewer = _invitee(UserRole.VIEWER)
        mock_user_repository.find_by_email.return_value = viewer
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = await _make_valid_code(viewer)

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        await use_case.execute(VerifyEmailRequest(email="new@example.com", code="ABC234", password="MyOwnPass123"))

        assert viewer.is_email_verified is True
        assert viewer.ai_credits_remaining == 0
        mock_workspace_repository.reserve_ai_credits.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_member_gets_only_what_is_left_under_the_workspace_ceiling(
        self, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        mock_workspace_repository.reserve_ai_credits.return_value = 2
        member = _invitee(UserRole.MEMBER)
        mock_user_repository.find_by_email.return_value = member
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = await _make_valid_code(member)

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        await use_case.execute(VerifyEmailRequest(email="new@example.com", code="ABC234", password="MyOwnPass123"))

        assert member.ai_credits_remaining == 2
        assert member.ai_credits_granted == 2

    @pytest.mark.asyncio
    async def test_an_invitee_sets_their_password_while_verifying(
        self, pending_user, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = await _make_valid_code(
            pending_user
        )

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        await use_case.execute(VerifyEmailRequest(email="new@example.com", code="ABC234", password="MyOwnPass123"))

        assert await PasswordHandler.verify_password("MyOwnPass123", pending_user.password_hash)
        assert pending_user.is_email_verified is True

    @pytest.mark.asyncio
    async def test_an_invitee_must_choose_a_password_and_keeps_the_code_until_then(
        self, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        invitee = UserEntity.create_workspace_member(
            email="new@example.com",
            display_name="Invitee",
            password_hash="placeholder",
            role=UserRole.MEMBER,
            workspace_id=EntityId.generate(),
        )
        mock_user_repository.find_by_email.return_value = invitee
        verification_code = await _make_valid_code(invitee)
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        with pytest.raises(ValueError, match="Choose a password"):
            await use_case.execute(_request())

        assert invitee.is_email_verified is False
        assert verification_code.used_at is None

    @pytest.mark.asyncio
    async def test_a_weak_password_is_rejected_without_burning_an_attempt(
        self, pending_user, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        verification_code = await _make_valid_code(pending_user)
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        with pytest.raises(ValueError, match="at least 8"):
            await use_case.execute(VerifyEmailRequest(email="new@example.com", code="ABC234", password="short"))

        assert verification_code.attempt_count == 0
        assert pending_user.is_email_verified is False

    @pytest.mark.asyncio
    async def test_code_is_accepted_regardless_of_case_and_whitespace(
        self, pending_user, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = await _make_valid_code(
            pending_user
        )

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        response = await use_case.execute(_request(code=" abc234 "))

        assert response.verified is True

    @pytest.mark.asyncio
    async def test_wrong_code_records_a_failed_attempt(
        self, pending_user, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        verification_code = await _make_valid_code(pending_user)
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request(code="ZZZ999"))

        assert verification_code.attempt_count == 1
        assert pending_user.is_email_verified is False
        mock_verification_code_repository.save.assert_awaited_once_with(verification_code)
        mock_user_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_expired_or_superseded_code_is_rejected(
        self, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        # The repository only returns unexpired, unused codes.
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = None

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request())

    @pytest.mark.asyncio
    async def test_code_is_locked_after_five_failed_attempts(
        self, pending_user, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        verification_code = await _make_valid_code(pending_user)
        verification_code.attempt_count = EmailVerificationCode.MAX_VALIDATION_ATTEMPTS
        mock_verification_code_repository.find_latest_active_by_user_id.return_value = verification_code

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        # Even the right code is refused once locked: a new code must be requested.
        with pytest.raises(VerificationRateLimitedError, match="request a new code"):
            await use_case.execute(_request())

        assert pending_user.is_email_verified is False

    @pytest.mark.asyncio
    async def test_unknown_email_gets_the_same_error_as_a_wrong_code(
        self, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        mock_user_repository.find_by_email.return_value = None

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request())

        mock_verification_code_repository.find_latest_active_by_user_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_already_verified_account_gets_the_same_error_as_a_wrong_code(
        self, pending_user, mock_user_repository, mock_verification_code_repository, mock_workspace_repository
    ):
        pending_user.verify_email()

        use_case = VerifyEmailUseCase(
            mock_user_repository, mock_verification_code_repository, mock_workspace_repository, LIMITS
        )
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(_request())

        mock_user_repository.update.assert_not_awaited()
