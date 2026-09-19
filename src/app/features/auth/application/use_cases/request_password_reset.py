"""RequestPasswordResetUseCase - Initiate password reset via emailed code."""

from src.app.features.auth.application.dtos.auth_dto import ForgotPasswordRequest, ForgotPasswordResponse
from src.app.features.auth.application.use_cases.issue_reset_code import GENERIC_RESET_MESSAGE, issue_reset_code
from src.app.features.auth.domain.repositories.password_reset_code_repository import PasswordResetCodeRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.logging import get_logger, mask_email


class RequestPasswordResetUseCase:
    """
    Sends a password reset code by email.

    Always returns the same generic response whether or not the email is
    registered, so the endpoint never discloses account existence (FR-009-01).
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

    async def execute(self, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        log = get_logger(__name__)
        email_lower = str(payload.email).lower().strip()

        user_entity = await self.user_repository.find_by_email(Email(email_lower))
        if user_entity is None:
            log.info(
                "Password reset requested for unknown email",
                extra={"event_type": "auth.password_reset.unknown_email", "email": mask_email(email_lower)},
            )
            return ForgotPasswordResponse(message=GENERIC_RESET_MESSAGE)

        await issue_reset_code(user_entity, self.reset_code_repository, self.email_sender)

        log.info(
            "Password reset code issued",
            extra={"event_type": "auth.password_reset.code_issued", "user_id": str(user_entity.id)},
        )
        return ForgotPasswordResponse(message=GENERIC_RESET_MESSAGE)
