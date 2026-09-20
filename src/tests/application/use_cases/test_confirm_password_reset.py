"""
Tests for ConfirmPasswordResetUseCase.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.app.features.auth.application.dtos.auth_dto import ResetPasswordRequest
from src.app.features.auth.application.use_cases.confirm_password_reset import ConfirmPasswordResetUseCase
from src.app.features.auth.application.use_cases.revoke_all_user_tokens import RevokeAllUserTokensUseCase
from src.app.features.auth.domain.entities.password_reset_code import PasswordResetCode
from src.app.features.auth.domain.exceptions.auth_exceptions import InvalidResetCodeError, ResetCodeRateLimitedError
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler


@pytest.fixture
def user_entity():
    return UserEntity(
        id=EntityId.generate(),
        email=Email("admin@example.com"),
        display_name="Admin User",
        password_hash="old-hash",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def mock_reset_code_repository():
    return AsyncMock()


@pytest.fixture
def revoke_all_use_case(mock_user_repository):
    return RevokeAllUserTokensUseCase(mock_user_repository)


async def _make_valid_code(user_entity, plain_code="ABC234"):
    code_hash = await PasswordHandler.hash_password(plain_code)
    return PasswordResetCode(
        id=EntityId.generate(),
        user_id=user_entity.id,
        code_hash=code_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )


class TestConfirmPasswordResetUseCase:
    @pytest.mark.asyncio
    async def test_valid_code_resets_password_and_revokes_sessions(
        self, user_entity, mock_user_repository, mock_reset_code_repository, revoke_all_use_case
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        mock_user_repository.find_by_id.return_value = user_entity
        reset_code = await _make_valid_code(user_entity)
        mock_reset_code_repository.find_latest_active_by_user_id.return_value = reset_code

        use_case = ConfirmPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, revoke_all_use_case)
        response = await use_case.execute(
            ResetPasswordRequest(email="admin@example.com", code="ABC234", new_password="NewPassw0rd")
        )

        assert response.message == "Password has been reset successfully."
        assert user_entity.password_hash != "old-hash"
        assert reset_code.used_at is not None
        mock_reset_code_repository.save.assert_awaited()
        mock_user_repository.update.assert_awaited()
        assert user_entity.token_version == 1  # forced logout after reset

    @pytest.mark.asyncio
    async def test_wrong_code_records_attempt_and_raises(
        self, user_entity, mock_user_repository, mock_reset_code_repository, revoke_all_use_case
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        reset_code = await _make_valid_code(user_entity, plain_code="ABC234")
        mock_reset_code_repository.find_latest_active_by_user_id.return_value = reset_code

        use_case = ConfirmPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, revoke_all_use_case)

        with pytest.raises(InvalidResetCodeError):
            await use_case.execute(
                ResetPasswordRequest(email="admin@example.com", code="WRONG1", new_password="NewPassw0rd")
            )

        assert reset_code.attempt_count == 1

    @pytest.mark.asyncio
    async def test_no_active_code_raises_invalid(
        self, user_entity, mock_user_repository, mock_reset_code_repository, revoke_all_use_case
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        mock_reset_code_repository.find_latest_active_by_user_id.return_value = None

        use_case = ConfirmPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, revoke_all_use_case)

        with pytest.raises(InvalidResetCodeError):
            await use_case.execute(
                ResetPasswordRequest(email="admin@example.com", code="ABC234", new_password="NewPassw0rd")
            )

    @pytest.mark.asyncio
    async def test_rate_limited_code_rejects_further_attempts(
        self, user_entity, mock_user_repository, mock_reset_code_repository, revoke_all_use_case
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        reset_code = await _make_valid_code(user_entity)
        reset_code.attempt_count = 5
        mock_reset_code_repository.find_latest_active_by_user_id.return_value = reset_code

        use_case = ConfirmPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, revoke_all_use_case)

        with pytest.raises(ResetCodeRateLimitedError):
            await use_case.execute(
                ResetPasswordRequest(email="admin@example.com", code="ABC234", new_password="NewPassw0rd")
            )

    @pytest.mark.asyncio
    async def test_weak_new_password_rejected_before_touching_code(
        self, user_entity, mock_user_repository, mock_reset_code_repository, revoke_all_use_case
    ):
        mock_user_repository.find_by_email.return_value = user_entity
        use_case = ConfirmPasswordResetUseCase(mock_user_repository, mock_reset_code_repository, revoke_all_use_case)

        with pytest.raises(ValueError):
            await use_case.execute(ResetPasswordRequest(email="admin@example.com", code="ABC234", new_password="short"))

        mock_reset_code_repository.find_latest_active_by_user_id.assert_not_called()
