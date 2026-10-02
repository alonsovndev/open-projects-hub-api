"""
RegisterUserUseCase - Public self sign-up pending email verification.

Following API spec requirements:
- Public endpoint (no auth required); every sign-up gets its own new, empty workspace
- Role: admin of that workspace, assigned server-side and never taken from the request
- Emails a verification code; the account cannot sign in until it is verified (FR-008-06)
- Returns RegisterResponse (masked email and code expiry, no tokens)
- Answers identically when a verified account already holds the email, and tells that
  account's owner by email instead, so the form cannot be used to probe for accounts
"""

from datetime import UTC, datetime, timedelta

from src.app.features.auth.application.dtos.auth_dto import RegisterRequest, RegisterResponse
from src.app.features.auth.application.services.email_links import EmailLinks
from src.app.features.auth.application.use_cases.issue_verification_code import (
    VERIFICATION_CODE_TTL_MINUTES,
    issue_verification_code,
)
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.features.workspaces.domain.entities.workspace_entity import WorkspaceEntity
from src.app.features.workspaces.domain.repositories.workspace_repository import WorkspaceRepository
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, mask_email, set_user_id


class RegisterUserUseCase:
    """
    Use case for user registration.

    Creates a new workspace with an unverified Admin and emails it a verification code.
    Two things are decided here rather than by the caller, because registration is
    anonymous: the role and the workspace. Either one taken from the request body would
    let a stranger into someone else's data.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        workspace_repository: WorkspaceRepository,
        verification_code_repository: EmailVerificationCodeRepository,
        email_sender: EmailSender,
        email_links: EmailLinks,
    ):
        self.user_repository = user_repository
        self.workspace_repository = workspace_repository
        self.verification_code_repository = verification_code_repository
        self.email_sender = email_sender
        self.email_links = email_links

    async def execute(self, payload: RegisterRequest) -> RegisterResponse:
        """
        Register a new user and email them a verification code.

        Args:
            payload: User registration data (email, password, displayName, optional workspaceName)

        Returns:
            RegisterResponse with the masked email and when the code expires

        Raises:
            ValueError: If validation fails
        """
        log = get_logger(__name__)
        set_user_id(str(payload.email))

        try:
            password_hash = await PasswordHandler.hash_password(payload.password)

            display_name = payload.display_name.strip()
            workspace = WorkspaceEntity.create(payload.workspace_name or WorkspaceEntity.default_name_for(display_name))
            new_user_entity = UserEntity.create_pending_verification(
                email=str(payload.email).lower().strip(),
                display_name=display_name,
                password_hash=password_hash,
                role=UserRole.ADMIN,
                workspace_id=workspace.id,
            )

            # Enforce email uniqueness constraint at application layer. Only a verified account
            # holds its address: a pending one (an abandoned sign-up, or someone another Admin
            # added) never proved ownership, so the real owner signing up replaces it.
            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user and existing_user.is_email_verified:
                log.warning(
                    "Registration attempt with existing email",
                    extra={"event_type": "auth.register.email_exists", "email": str(new_user_entity.email)},
                )
                return await self._answer_for_existing_account(str(new_user_entity.email))

            if existing_user:
                log.info(
                    "Registration replaces an unverified account",
                    extra={"event_type": "auth.register.replaces_pending", "user_id": str(existing_user.id)},
                )

            created_user = await self.workspace_repository.create_with_admin(
                workspace, new_user_entity, replacing=existing_user
            )

            # Handle race condition where another request created the user between check and save
            if created_user is None:
                log.warning(
                    "Race condition during registration",
                    extra={"event_type": "auth.register.race_condition", "email": str(new_user_entity.email)},
                )
                return await self._answer_for_existing_account(str(new_user_entity.email))

            code_expires_at = await issue_verification_code(
                created_user, self.verification_code_repository, self.email_sender, self.email_links
            )

            log.info(
                "User registered, pending email verification",
                extra={"event_type": "auth.register.success", "user_id": str(created_user.id.value)},
            )
            return RegisterResponse(
                email=mask_email(str(created_user.email.value)),
                code_expires_at=code_expires_at.isoformat(),
            )

        except ValueError:
            raise
        except Exception:
            log.exception(
                "Unexpected error in RegisterUserUseCase", extra={"event_type": "auth.register.unexpected_error"}
            )
            raise

    async def _answer_for_existing_account(self, email: str) -> RegisterResponse:
        """Email the account's owner and return what a fresh sign-up would, so callers can't tell them apart."""
        try:
            await self.email_sender.send(
                to=email,
                subject="You already have an Open Projects Hub account",
                body=(
                    "Someone tried to create an account with this email, but you already have one.\n\n"
                    f"Sign in: {self.email_links.sign_in()}\n\n"
                    'If you forgot your password, use "Forgot password" on the sign-in page.\n\n'
                    "If this wasn't you, you can ignore this email."
                ),
            )
        except Exception:
            get_logger(__name__).exception(
                "Existing-account notice failed to send",
                extra={"event_type": "auth.register.notice_email_failed", "email": mask_email(email)},
            )

        decoy_expires_at = datetime.now(UTC) + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES)
        return RegisterResponse(email=mask_email(email), code_expires_at=decoy_expires_at.isoformat())
