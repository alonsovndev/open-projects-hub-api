"""
RegisterUserUseCase - Public registration pending email verification.

Following API spec requirements:
- Public endpoint (no auth required), open only while the instance has no accounts
- Role: admin, assigned server-side and never taken from the request
- Emails a verification code; the account cannot sign in until it is verified (FR-008-06)
- Returns RegisterResponse (masked email and code expiry, no tokens)
"""

from src.app.features.auth.application.dtos.auth_dto import RegisterRequest, RegisterResponse
from src.app.features.auth.application.use_cases.issue_verification_code import issue_verification_code
from src.app.features.auth.domain.exceptions.auth_exceptions import RegistrationClosedError
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, mask_email, set_user_id


class RegisterUserUseCase:
    """
    Use case for user registration.

    Bootstraps the instance's first Admin as an unverified account and emails it a
    verification code. Two things are decided here rather than by the caller, because
    registration is anonymous: whether it is still open at all, and the role. Either one
    left to the request body would be a privilege-escalation path.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        verification_code_repository: EmailVerificationCodeRepository,
        email_sender: EmailSender,
    ):
        self.user_repository = user_repository
        self.verification_code_repository = verification_code_repository
        self.email_sender = email_sender

    async def execute(self, payload: RegisterRequest) -> RegisterResponse:
        """
        Register a new user and email them a verification code.

        Args:
            payload: User registration data (email, password, displayName)

        Returns:
            RegisterResponse with the masked email and when the code expires

        Raises:
            RegistrationClosedError: If the instance already has an account
            UserAlreadyExistsError: If email already exists
            ValueError: If validation fails
        """
        log = get_logger(__name__)
        set_user_id(str(payload.email))

        try:
            if await self.user_repository.exists_any():
                log.warning(
                    "Registration attempt on an instance that already has accounts",
                    extra={"event_type": "auth.register.closed", "email": str(payload.email)},
                )
                raise RegistrationClosedError

            password_hash = await PasswordHandler.hash_password(payload.password)

            new_user_entity = UserEntity.create_pending_verification(
                email=str(payload.email).lower().strip(),
                display_name=payload.display_name.strip(),
                password_hash=password_hash,
                role=UserRole.ADMIN,
            )

            # Enforce email uniqueness constraint at application layer
            existing_user = await self.user_repository.find_by_email(new_user_entity.email)

            if existing_user:
                log.warning(
                    "Registration attempt with existing email",
                    extra={"event_type": "auth.register.email_exists", "email": str(new_user_entity.email)},
                )
                raise UserAlreadyExistsError(str(new_user_entity.email))

            created_user = await self.user_repository.save(new_user_entity)

            # Handle race condition where another request created the user between check and save
            if created_user is None:
                log.warning(
                    "Race condition during registration",
                    extra={"event_type": "auth.register.race_condition", "email": str(new_user_entity.email)},
                )
                raise UserAlreadyExistsError(str(new_user_entity.email))

            code_expires_at = await issue_verification_code(
                created_user, self.verification_code_repository, self.email_sender
            )

            log.info(
                "User registered, pending email verification",
                extra={"event_type": "auth.register.success", "user_id": str(created_user.id.value)},
            )
            return RegisterResponse(
                email=mask_email(str(created_user.email.value)),
                code_expires_at=code_expires_at.isoformat(),
            )

        except (ValueError, UserAlreadyExistsError, RegistrationClosedError):
            raise
        except Exception:
            log.exception(
                "Unexpected error in RegisterUserUseCase", extra={"event_type": "auth.register.unexpected_error"}
            )
            raise
