"""
Shared code-issuing logic used by RequestPasswordResetUseCase and
ResendResetCodeUseCase — generating, hashing, persisting, and emailing a
password reset code (FR-009-02).
"""

import secrets
from datetime import UTC, datetime, timedelta

from src.app.features.auth.domain.entities.password_reset_code import PasswordResetCode
from src.app.features.auth.domain.repositories.password_reset_code_repository import PasswordResetCodeRepository
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.email.email_sender import EmailSender
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, mask_email


# Excludes 0, 1, O, I (visually ambiguous) per FR-009-02.
RESET_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
RESET_CODE_LENGTH = 6
RESET_CODE_TTL_MINUTES = 5
GENERIC_RESET_MESSAGE = "If an account exists for this email, a reset code has been sent."


def generate_reset_code() -> str:
    return "".join(secrets.choice(RESET_CODE_ALPHABET) for _ in range(RESET_CODE_LENGTH))


async def issue_reset_code(
    user_entity: UserEntity,
    reset_code_repository: PasswordResetCodeRepository,
    email_sender: EmailSender,
) -> None:
    """Invalidate any active code for the user, then generate, persist, and email a new one."""
    await reset_code_repository.invalidate_active_for_user(user_entity.id)

    code = generate_reset_code()
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
            body=f"Your password reset code is {code}. It expires in {RESET_CODE_TTL_MINUTES} minutes.",
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
