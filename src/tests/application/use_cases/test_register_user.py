"""
Tests for RegisterUserUseCase.

Following API spec:
- POST /auth/register creates a new workspace with an unverified Admin and emails a code
- Role and workspace are decided server-side; never taken from the request
- Returns RegisterResponse (masked email, code expiry) and no tokens
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.app.features.auth.application.dtos.auth_dto import RegisterRequest, RegisterResponse
from src.app.features.auth.application.services.email_links import EmailLinks
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId


def build_open_instance_repo() -> AsyncMock:
    """A user repository in which the email is not yet taken."""
    user_repository = AsyncMock()
    user_repository.find_by_email.return_value = None
    return user_repository


def build_workspace_repository() -> AsyncMock:
    """create_with_admin echoes the admin, as the real one does on success."""
    workspace_repository = AsyncMock()
    workspace_repository.create_with_admin.side_effect = lambda _workspace, admin, **_scope: admin
    return workspace_repository


def build_use_case(user_repository: AsyncMock) -> tuple[RegisterUserUseCase, AsyncMock, AsyncMock]:
    verification_code_repository = AsyncMock()
    email_sender = AsyncMock()
    use_case = RegisterUserUseCase(
        user_repository,
        build_workspace_repository(),
        verification_code_repository,
        email_sender,
        EmailLinks("http://localhost:5173"),
    )
    return use_case, verification_code_repository, email_sender


def saved_admin(use_case: RegisterUserUseCase) -> UserEntity:
    return use_case.workspace_repository.create_with_admin.call_args[0][1]


def saved_workspace(use_case: RegisterUserUseCase):
    return use_case.workspace_repository.create_with_admin.call_args[0][0]


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
        saved_entity = saved_admin(use_case)
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
                role="member",
            )

        await use_case.execute(build_payload())

        assert saved_admin(use_case).role is UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_execute_creates_an_unverified_account_without_credits(self):
        """FR-008-06 / FR-010-01: no sign-in and no free credits until the email is verified."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(build_payload())

        saved_entity = saved_admin(use_case)
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
    async def test_the_registration_email_links_to_verification_without_a_password_step(self):
        user_repository = build_open_instance_repo()
        use_case, _, email_sender = build_use_case(user_repository)

        await use_case.execute(build_payload())

        body = email_sender.send.call_args.kwargs["body"]
        assert "http://localhost:5173/verify-email?email=newuser%40example.com&code=" in body
        assert "setPassword" not in body
        assert "5 minutes" in body

    @pytest.mark.asyncio
    async def test_execute_still_registers_when_the_email_fails_to_send(self):
        """The user can recover with a resend, so a delivery failure must not fail registration."""
        user_repository = build_open_instance_repo()
        use_case, _, email_sender = build_use_case(user_repository)
        email_sender.send.side_effect = ConnectionError("SMTP down")

        result = await use_case.execute(build_payload())

        assert result.verification_required is True

    @pytest.mark.asyncio
    async def test_execute_answers_like_a_new_sign_up_when_email_exists(self):
        """A verified email must not be distinguishable from a free one; its owner is told by email."""
        existing_user = UserEntity(
            id=EntityId.generate(),
            email=Email("existing@example.com"),
            display_name="Existing User",
            password_hash="hashed",
            role=UserRole.ADMIN,
            email_verified_at=datetime.now(UTC),
        )
        user_repository = build_open_instance_repo()
        user_repository.find_by_email.return_value = existing_user
        use_case, verification_code_repository, email_sender = build_use_case(user_repository)

        result = await use_case.execute(build_payload("existing@example.com"))

        assert result.verification_required is True
        assert result.code_expires_at
        use_case.workspace_repository.create_with_admin.assert_not_called()
        verification_code_repository.create.assert_not_called()
        email_sender.send.assert_called_once()
        assert email_sender.send.call_args.kwargs["to"] == "existing@example.com"
        assert "already have" in email_sender.send.call_args.kwargs["body"]

    @pytest.mark.asyncio
    async def test_execute_hashes_password_before_storing(self):
        """Test that password is hashed, not stored in plain text."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(
            RegisterRequest(display_name="Test User", email="user@example.com", password="PlainPassword123")
        )

        saved_entity = saved_admin(use_case)
        assert saved_entity.password_hash != "PlainPassword123"
        assert saved_entity.password_hash.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_execute_converts_email_to_lowercase(self):
        """Test that email is normalized to lowercase."""
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(build_payload("User@Example.COM"))

        assert saved_admin(use_case).email.value == "user@example.com"

    @pytest.mark.asyncio
    async def test_execute_registers_even_when_other_accounts_exist(self):
        """Sign-up is open: each account gets its own workspace, so others' data stays out of reach."""
        user_repository = build_open_instance_repo()
        use_case, _, email_sender = build_use_case(user_repository)

        result = await use_case.execute(build_payload())

        assert result.verification_required is True
        email_sender.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_creates_a_new_workspace_owned_by_the_admin(self):
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(build_payload())

        workspace = saved_workspace(use_case)
        assert saved_admin(use_case).workspace_id == workspace.id
        assert workspace.name == "New User's workspace"

    @pytest.mark.asyncio
    async def test_execute_uses_the_requested_workspace_name(self):
        user_repository = build_open_instance_repo()
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(
            RegisterRequest(
                display_name="New User", email="a@example.com", password="SecurePass123", workspace_name=" Acme "
            )
        )

        assert saved_workspace(use_case).name == "Acme"

    @pytest.mark.asyncio
    async def test_execute_answers_like_a_new_sign_up_when_the_email_is_taken_concurrently(self):
        """The workspace insert and the admin insert commit together, so a lost race persists nothing."""
        user_repository = build_open_instance_repo()
        use_case, verification_code_repository, email_sender = build_use_case(user_repository)
        use_case.workspace_repository.create_with_admin.side_effect = None
        use_case.workspace_repository.create_with_admin.return_value = None

        result = await use_case.execute(build_payload())

        assert result.verification_required is True
        verification_code_repository.create.assert_not_called()
        email_sender.send.assert_called_once()


class TestRegisterOverPendingAccounts:
    """Only a verified account holds its email; a pending one must not lock the owner out."""

    @staticmethod
    def pending_account(role: UserRole) -> UserEntity:
        return UserEntity.create_workspace_member(
            email="owner@example.com",
            display_name="Squatted",
            password_hash="hash",
            role=role,
            workspace_id=EntityId.generate(),
        )

    @pytest.mark.asyncio
    async def test_an_unverified_account_is_replaced_by_the_real_sign_up(self):
        pending = self.pending_account(UserRole.MEMBER)
        user_repository = build_open_instance_repo()
        user_repository.find_by_email.return_value = pending
        use_case, _, email_sender = build_use_case(user_repository)

        await use_case.execute(build_payload("owner@example.com"))

        assert use_case.workspace_repository.create_with_admin.call_args.kwargs["replacing"] is pending
        assert saved_admin(use_case).role is UserRole.ADMIN
        email_sender.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_a_verified_account_is_never_replaced(self):
        verified = self.pending_account(UserRole.MEMBER)
        verified.verify_email()
        user_repository = build_open_instance_repo()
        user_repository.find_by_email.return_value = verified
        use_case, _, _ = build_use_case(user_repository)

        await use_case.execute(build_payload("owner@example.com"))

        use_case.workspace_repository.create_with_admin.assert_not_called()
