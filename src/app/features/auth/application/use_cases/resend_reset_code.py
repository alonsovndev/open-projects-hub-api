"""ResendResetCodeUseCase - Reissue a password reset code within rate limits."""

from datetime import UTC, datetime, timedelta

from src.app.features.auth.application.dtos.auth_dto import ForgotPasswordResponse, ResendResetCodeRequest
from src.app.features.auth.application.use_cases.issue_reset_code import GENERIC_RESET_MESSAGE, issue_reset_code
from src.app.features.auth.domain.exceptions.auth_exceptions import ResetCodeRateLimitedError
from src.app.features.auth.domain.repositories.password_reset_code_repository import PasswordResetCodeRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.logging import get_logger, mask_email


RESEND_WINDOW_MINUTES = 15
MAX_RESENDS_PER_WINDOW = 3


class ResendResetCodeUseCase:
    """
    Reissues a password reset code, invalidating the previous one.

    Enforces FR-009-04: at most 3 codes per email within a 15-minute window.
    Silently no-ops (same generic response) for unknown emails, matching
    RequestPasswordResetUseCase's non-enumeration behavior.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        reset_code_repository: PasswordResetCodeRepository,
        email_sender: EmailSender,
    ):
        self.user_repository = user_repository
        self.reset_code_repository = reset_code_repository
        self.email_sender = email_sender

    async def execute(self, payload: ResendResetCodeRequest) -> ForgotPasswordResponse:
        log = get_logger(__name__)
        email_lower = str(payload.email).lower().strip()

        user_entity = await self.user_repository.find_by_email(Email(email_lower))
        if user_entity is None:
            return ForgotPasswordResponse(message=GENERIC_RESET_MESSAGE)

        window_start = datetime.now(UTC) - timedelta(minutes=RESEND_WINDOW_MINUTES)
        recent_count = await self.reset_code_repository.count_created_since(user_entity.id, window_start)
        if recent_count >= MAX_RESENDS_PER_WINDOW:
            log.warning(
                "Password reset resend rate-limited",
                extra={"event_type": "auth.password_reset.resend_rate_limited", "email": mask_email(email_lower)},
            )
            raise ResetCodeRateLimitedError("Too many reset code requests. Please try again later.")

        await issue_reset_code(user_entity, self.reset_code_repository, self.email_sender)

        log.info(
            "Password reset code resent",
            extra={"event_type": "auth.password_reset.code_resent", "user_id": str(user_entity.id)},
        )
        return ForgotPasswordResponse(message=GENERIC_RESET_MESSAGE)
