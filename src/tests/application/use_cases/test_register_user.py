"""
Tests for RegisterUserUseCase.

Following API spec:
- POST /auth/register creates an unverified account and emails a verification code
- Role is assigned server-side (admin); never taken from the request
- Returns RegisterResponse (masked email, code expiry) and no tokens
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.app.features.auth.application.dtos.auth_dto import RegisterRequest, RegisterResponse
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import RegistrationClosedError
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


def build_open_instance_repo() -> AsyncMock:
    """A user repository for an instance with no accounts yet; save echoes the entity."""
    user_repository = AsyncMock()
    user_repository.exists_any.return_value = False
    user_repository.find_by_email.return_value = None
    user_repository.save.side_effect = lambda user_entity: user_entity
    return user_repository


def build_use_case(user_repository: AsyncMock) -> tuple[RegisterUserUseCase, AsyncMock, AsyncMock]:
    verification_code_repository = AsyncMock()
    email_sender = AsyncMock()
    use_case = RegisterUserUseCase(user_repository, verification_code_repository, email_sender)
    return use_case, verification_code_repository, email_sender


def build_payload(email: str = "newuser@example.com") -> RegisterRequest:
    return RegisterRequest(display_name="New User", email=email, password="SecurePass123")


class TestRegisterUserUseCase:
    """Test RegisterUserUseCase functionality."""

    @pytest.mark.asyncio
    async def test_execute_creates_user_with_admin_role(self):
        """Test that registration creates the account with the admin role."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(build_payload())

        # Assert on the entity the use case built, not on a stubbed return value —
        # otherwise the mock, not the code under test, decides the role.
        saved_entity = user_repository.save.call_args[0][0]
        assert saved_entity.role is UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_execute_ignores_a_role_supplied_by_the_caller(self):
        """A role in the request body must not reach the entity: registration is anonymous."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        with pytest.raises(PydanticValidationError):
            RegisterRequest(
                display_name="New User",
                email="newuser@example.com",
                password="SecurePass123",
                role="viewer",
            )

        await use_case.execute(build_payload())

        assert user_repository.save.call_args[0][0].role is UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_execute_creates_an_unverified_account_without_credits(self):
        """FR-008-06 / FR-010-01: no sign-in and no free credits until the email is verified."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(build_payload())

        saved_entity = user_repository.save.call_args[0][0]
        assert saved_entity.is_email_verified is False
        assert saved_entity.ai_credits_remaining == 0

    @pytest.mark.asyncio
    async def test_execute_returns_a_pending_verification_response_without_tokens(self):
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        result = await use_case.execute(build_payload("newuser@example.com"))

        assert isinstance(result, RegisterResponse)
        assert result.email == "ne***@example.com"
        assert result.verification_required is True
        assert result.next_step == "verify-email"
        assert datetime.fromisoformat(result.code_expires_at) > datetime.now(UTC)
        assert not hasattr(result, "token")

    @pytest.mark.asyncio
    async def test_execute_emails_a_hashed_verification_code(self):
        user_repository = build_open_instance_repo()
        use_case, verification_code_repository, email_sender = build_use_case(user_repository)

        await use_case.execute(build_payload())

        stored_code = verification_code_repository.create.call_args[0][0]
        sent_email = email_sender.send.call_args.kwargs
        assert sent_email["to"] == "newuser@example.com"
        assert sent_email["subject"] == "Verify your email"
        assert stored_code.code_hash.startswith("$2b$")
        assert stored_code.code_hash not in sent_email["body"]

    @pytest.mark.asyncio
    async def test_execute_still_registers_when_the_email_fails_to_send(self):
        """The user can recover with a resend, so a delivery failure must not fail registration."""
        user_repository = build_open_instance_repo()
        use_case, _, email_sender = build_use_case(user_repository)
        email_sender.send.side_effect = ConnectionError("SMTP down")

        result = await use_case.execute(build_payload())

        assert result.verification_required is True

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_email_exists(self):
        """Test that duplicate email raises UserAlreadyExistsError."""
        existing_user = UserEntity(
            id=EntityId.generate(),
            email=Email("existing@example.com"),
            display_name="Existing User",
            password_hash="hashed",
            role=UserRole.ADMIN,
        )
        user_repository = build_open_instance_repo()
        user_repository.find_by_email.return_value = existing_user
        use_case, _, email_sender = build_use_case(user_repository)

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await use_case.execute(build_payload("existing@example.com"))

        assert "existing@example.com" in str(exc_info.value)
        user_repository.save.assert_not_called()
        email_sender.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_hashes_password_before_storing(self):
        """Test that password is hashed, not stored in plain text."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(
            RegisterRequest(display_name="Test User", email="user@example.com", password="PlainPassword123")
        )

        saved_entity = user_repository.save.call_args[0][0]
        assert saved_entity.password_hash != "PlainPassword123"
        assert saved_entity.password_hash.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_execute_converts_email_to_lowercase(self):
        """Test that email is normalized to lowercase."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(build_payload("User@Example.COM"))

        assert user_repository.save.call_args[0][0].email.value == "user@example.com"

    @pytest.mark.asyncio
    async def test_execute_rejects_registration_once_an_account_exists(self):
        """Registration bootstraps the first Admin only; after that it is closed.

        Left open it would hand any anonymous caller an Admin account, which would walk
        straight through every role boundary in F-003.
        """
        user_repository = build_open_instance_repo()
        user_repository.exists_any.return_value = True
        use_case, _, email_sender = build_use_case(user_repository)

        with pytest.raises(RegistrationClosedError):
            await use_case.execute(build_payload())

        user_repository.save.assert_not_called()
        email_sender.send.assert_not_called()
