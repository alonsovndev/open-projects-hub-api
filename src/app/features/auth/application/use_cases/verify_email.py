"""VerifyEmailUseCase - Confirm a self-registered account's email with its code."""

from src.app.features.auth.application.dtos.auth_dto import VerifyEmailRequest, VerifyEmailResponse
from src.app.features.auth.domain.exceptions.auth_exceptions import (
    InvalidVerificationCodeError,
    VerificationRateLimitedError,
)
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, mask_email


class VerifyEmailUseCase:
    """
    Validates a verification code, marks the account verified, and grants its free credits.

    Enforces NFR-008-03: after 5 wrong guesses the code is locked and a new one must be
    requested. Unknown emails, already-verified accounts, and missing codes all raise the
    same InvalidVerificationCodeError so the endpoint discloses nothing about accounts.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        verification_code_repository: EmailVerificationCodeRepository,
    ):
        self.user_repository = user_repository
        self.verification_code_repository = verification_code_repository

    async def execute(self, payload: VerifyEmailRequest) -> VerifyEmailResponse:
        log = get_logger(__name__)
        email_lower = str(payload.email).lower().strip()

        user_entity = await self.user_repository.find_by_email(Email(email_lower))
        if user_entity is None or user_entity.is_email_verified:
            raise InvalidVerificationCodeError

        verification_code = await self.verification_code_repository.find_latest_active_by_user_id(user_entity.id)
        if verification_code is None:
            raise InvalidVerificationCodeError

        if verification_code.is_rate_limited():
            raise VerificationRateLimitedError("Too many attempts. Please request a new code.")

        # Codes are issued uppercase; accept them however the user typed them.
        submitted_code = payload.code.strip().upper()
        if not await PasswordHandler.verify_password(submitted_code, verification_code.code_hash):
            verification_code.record_failed_attempt()
            await self.verification_code_repository.save(verification_code)
            log.warning(
                "Invalid email verification code",
                extra={
                    "event_type": "auth.verify_email.invalid_code",
                    "email": mask_email(email_lower),
                    "attempt_count": verification_code.attempt_count,
                },
            )
            raise InvalidVerificationCodeError

        verification_code.mark_used()
        await self.verification_code_repository.save(verification_code)

        user_entity.verify_email()
        await self.user_repository.update(user_entity)

        log.info(
            "Email verified",
            extra={"event_type": "auth.verify_email.success", "user_id": str(user_entity.id)},
        )
        return VerifyEmailResponse(verified=True)
