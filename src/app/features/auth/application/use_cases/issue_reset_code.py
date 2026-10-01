"""
Shared code-issuing logic used by RequestPasswordResetUseCase and
ResendResetCodeUseCase — generating, hashing, persisting, and emailing a
password reset code (FR-009-02).
"""

from datetime import UTC, datetime, timedelta

from src.app.features.auth.application.services.email_links import EmailLinks
from src.app.features.auth.application.services.one_time_code import generate_one_time_code
from src.app.features.auth.domain.entities.password_reset_code import PasswordResetCode
from src.app.features.auth.domain.repositories.password_reset_code_repository import PasswordResetCodeRepository
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, mask_email


RESET_CODE_TTL_MINUTES = 30
GENERIC_RESET_MESSAGE = "If an account exists for this email, a reset code has been sent."

# NFR-009-02 caps code requests per email, not per endpoint, so both the initial
# request and the resend path count against the same window.
REQUEST_WINDOW_MINUTES = 15
MAX_REQUESTS_PER_WINDOW = 3


async def is_request_rate_limited(
    user_id: EntityId,
    reset_code_repository: PasswordResetCodeRepository,
) -> bool:
    """Whether this user has already been issued the window's allowance of codes."""
    window_start = datetime.now(UTC) - timedelta(minutes=REQUEST_WINDOW_MINUTES)
    recent_count = await reset_code_repository.count_created_since(user_id, window_start)
    return recent_count >= MAX_REQUESTS_PER_WINDOW


async def issue_reset_code(
    user_entity: UserEntity,
    reset_code_repository: PasswordResetCodeRepository,
    email_sender: EmailSender,
    email_links: EmailLinks,
) -> None:
    """Invalidate any active code for the user, then generate, persist, and email a new one."""
    await reset_code_repository.invalidate_active_for_user(user_entity.id)

    code = generate_one_time_code()
    code_hash = await PasswordHandler.hash_password(code)
    reset_code = PasswordResetCode(
        id=EntityId.generate(),
        user_id=user_entity.id,
        code_hash=code_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=RESET_CODE_TTL_MINUTES),
    )
    await reset_code_repository.create(reset_code)

    try:
        await email_sender.send(
            to=str(user_entity.email),
            subject="Your password reset code",
            body=(
                f"Your password reset code is {code}.\n\n"
                f"Or reset directly: {email_links.reset_password(str(user_entity.email), code)}\n\n"
                f"It expires in {RESET_CODE_TTL_MINUTES} minutes.\n\n"
                "If you didn't ask for this, you can ignore this email."
            ),
        )
    except Exception:
        # Never let a delivery failure surface to the caller: the reset-code
        # endpoints return the same generic response regardless of whether
        # the email exists, and a differing outcome here (500 vs 200) would
        # reopen that as an account-enumeration side channel.
        get_logger(__name__).exception(
            "Password reset email failed to send",
            extra={"event_type": "auth.password_reset.email_failed", "email": mask_email(str(user_entity.email))},
        )
