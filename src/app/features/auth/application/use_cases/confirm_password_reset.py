"""ConfirmPasswordResetUseCase - Complete a password reset with a valid code."""

from src.app.features.auth.application.dtos.auth_dto import ResetPasswordRequest, ResetPasswordResponse
from src.app.features.auth.application.use_cases.revoke_all_user_tokens import RevokeAllUserTokensUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import InvalidResetCodeError, ResetCodeRateLimitedError
from src.app.features.auth.domain.repositories.password_reset_code_repository import PasswordResetCodeRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.validators.user_validators import UserValidators
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, mask_email


class ConfirmPasswordResetUseCase:
    """
    Validates a reset code and applies the new password (FR-009-05).

    On success, revokes every existing session for the user
    (RevokeAllUserTokensUseCase) so a compromised account can't remain
    logged in elsewhere after recovery.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        reset_code_repository: PasswordResetCodeRepository,
        revoke_all_tokens_use_case: RevokeAllUserTokensUseCase,
    ):
        self.user_repository = user_repository
        self.reset_code_repository = reset_code_repository
        self.revoke_all_tokens_use_case = revoke_all_tokens_use_case

    async def execute(self, payload: ResetPasswordRequest) -> ResetPasswordResponse:
        log = get_logger(__name__)
        email_lower = str(payload.email).lower().strip()

        # Validate the new password up front so a malformed request never
        # burns a validation attempt against an otherwise-valid code.
        UserValidators.validate_password(payload.new_password)

        user_entity = await self.user_repository.find_by_email(Email(email_lower))
        if user_entity is None:
            log.warning(
                "Password reset confirm for unknown email",
                extra={"event_type": "auth.password_reset.confirm_unknown_email", "email": mask_email(email_lower)},
            )
            raise InvalidResetCodeError()

        # find_latest_active_by_user_id already excludes expired/used codes,
        # so a miss here covers both "no code requested" and "code expired".
        reset_code = await self.reset_code_repository.find_latest_active_by_user_id(user_entity.id)
        if reset_code is None:
            raise InvalidResetCodeError()

        if reset_code.is_rate_limited():
            raise ResetCodeRateLimitedError("Too many attempts. Please request a new code.")

        code_valid = await PasswordHandler.verify_password(payload.code, reset_code.code_hash)
        if not code_valid:
            reset_code.record_failed_attempt()
            await self.reset_code_repository.save(reset_code)
            raise InvalidResetCodeError()

        new_password_hash = await PasswordHandler.hash_password(payload.new_password)
        user_entity.update_details(password_hash=new_password_hash)
        await self.user_repository.update(user_entity)

        reset_code.mark_used()
        await self.reset_code_repository.save(reset_code)

        await self.revoke_all_tokens_use_case.execute(user_entity.id)

        log.info(
            "Password reset completed",
            extra={"event_type": "auth.password_reset.success", "user_id": str(user_entity.id)},
        )
        return ResetPasswordResponse(message="Password has been reset successfully.")
