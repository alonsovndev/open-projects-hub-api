"""ResendVerificationUseCase - Reissue an email verification code within rate limits."""

from src.app.features.auth.application.dtos.auth_dto import ResendVerificationRequest, ResendVerificationResponse
from src.app.features.auth.application.use_cases.issue_verification_code import (
    GENERIC_RESEND_MESSAGE,
    is_verification_rate_limited,
    issue_verification_code,
)
from src.app.features.auth.domain.exceptions.auth_exceptions import VerificationRateLimitedError
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.logging import get_logger, mask_email


class ResendVerificationUseCase:
    """
    Reissues a verification code, invalidating the previous one.

    Enforces FR-008-05: 3 resends per email within 15 minutes, on top of the code sent at
    registration (see issue_verification_code.is_verification_rate_limited). Unknown and
    already-verified emails get the same generic response with no email sent.
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

    async def execute(self, payload: ResendVerificationRequest) -> ResendVerificationResponse:
        log = get_logger(__name__)
        email_lower = str(payload.email).lower().strip()

        user_entity = await self.user_repository.find_by_email(Email(email_lower))
        if user_entity is None or user_entity.is_email_verified:
            return ResendVerificationResponse(message=GENERIC_RESEND_MESSAGE)

        if await is_verification_rate_limited(user_entity.id, self.verification_code_repository):
            log.warning(
                "Verification code resend rate-limited",
                extra={"event_type": "auth.verify_email.resend_rate_limited", "email": mask_email(email_lower)},
            )
            raise VerificationRateLimitedError("Too many code requests. Please try again in 15 minutes.")

        await issue_verification_code(user_entity, self.verification_code_repository, self.email_sender)

        log.info(
            "Verification code resent",
            extra={"event_type": "auth.verify_email.code_resent", "user_id": str(user_entity.id)},
        )
        return ResendVerificationResponse(message=GENERIC_RESEND_MESSAGE)
