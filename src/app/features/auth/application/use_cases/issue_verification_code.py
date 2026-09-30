"""
Shared code-issuing logic used by RegisterUserUseCase and
ResendVerificationUseCase — generating, hashing, persisting, and emailing an
email verification code (FR-008-03 to FR-008-05).
"""

from datetime import UTC, datetime, timedelta

from src.app.features.auth.application.services.one_time_code import generate_one_time_code
from src.app.features.auth.domain.entities.email_verification_code import EmailVerificationCode
from src.app.features.auth.domain.repositories.email_verification_code_repository import EmailVerificationCodeRepository
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, mask_email


VERIFICATION_CODE_TTL_MINUTES = 5
GENERIC_RESEND_MESSAGE = "If this email is awaiting verification, a new code has been sent."

# FR-008-05 allows 3 resends per 15 minutes on top of the code sent at registration,
# and codes are counted per email across both paths.
RESEND_WINDOW_MINUTES = 15
MAX_CODES_PER_WINDOW = 4


async def is_verification_rate_limited(
    user_id: EntityId,
    verification_code_repository: EmailVerificationCodeRepository,
) -> bool:
    """Whether this user has already been issued the window's allowance of codes."""
    window_start = datetime.now(UTC) - timedelta(minutes=RESEND_WINDOW_MINUTES)
    recent_count = await verification_code_repository.count_created_since(user_id, window_start)
    return recent_count >= MAX_CODES_PER_WINDOW


async def issue_verification_code(
    user_entity: UserEntity,
    verification_code_repository: EmailVerificationCodeRepository,
    email_sender: EmailSender,
) -> datetime:
    """
    Invalidate any active code for the user, then generate, persist, and email a new one.

    Returns:
        When the new code expires.
    """
    await verification_code_repository.invalidate_active_for_user(user_entity.id)

    code = generate_one_time_code()
    code_hash = await PasswordHandler.hash_password(code)
    expires_at = datetime.now(UTC) + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES)
    await verification_code_repository.create(
        EmailVerificationCode(
            id=EntityId.generate(),
            user_id=user_entity.id,
            code_hash=code_hash,
            expires_at=expires_at,
        )
    )

    try:
        await email_sender.send(
            to=str(user_entity.email),
            subject="Verify your email",
            body=(
                f"Your Open Projects Hub verification code is {code}.\n\n"
                f"It expires in {VERIFICATION_CODE_TTL_MINUTES} minutes.\n\n"
                "If you didn't create an account, you can ignore this email."
            ),
        )
    except Exception:
        # The account and code already exist, so the user can recover with a resend;
        # failing the request here would leave them registered with no way to know.
        get_logger(__name__).exception(
            "Verification email failed to send",
            extra={"event_type": "auth.verify_email.email_failed", "email": mask_email(str(user_entity.email))},
        )

    return expires_at
