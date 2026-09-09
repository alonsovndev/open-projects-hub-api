"""
ChangePasswordUseCase - Change user password with verification.

Requires current password verification before updating to new password.
"""

from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.validators.user_validators import UserValidators
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, set_user_id


class ChangePasswordUseCase:
    """
    Use case for changing user password.

    Verifies current password before updating to new password with validation.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, current_password: str, new_password: str) -> None:
        """
        Change user password.

        Args:
            user_id: UUID string of the user (extracted from JWT)
            current_password: Current password for verification
            new_password: New password (min 8 chars, letter + digit)

        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If validation fails or current password incorrect
        """
        log = get_logger(__name__)
        set_user_id(user_id)

        try:
            # Validate new password
            UserValidators.validate_password(new_password)

            # Find user
            user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))

            if user_entity is None:
                log.warning(
                    "User not found for password change",
                    extra={"event_type": "user.password.change.user_not_found", "user_id": user_id},
                )
                raise UserNotFoundError(user_id)

            # Verify current password
            is_valid = await PasswordHandler.verify_password(current_password, user_entity.password_hash)

            if not is_valid:
                log.warning(
                    "Incorrect current password for password change",
                    extra={"event_type": "user.password.change.incorrect_password", "user_id": user_id},
                )
                raise ValueError("Current password is incorrect")

            # Hash new password
            new_password_hash = await PasswordHandler.hash_password(new_password)

            # Update password hash
            user_entity.update_details(password_hash=new_password_hash)

            # Save updated entity
            await self.user_repository.save(user_entity)

            log.info("Password changed", extra={"event_type": "user.password.changed"})

        except (UserNotFoundError, ValueError):
            raise
        except Exception:
            log.exception(
                "Unexpected error changing password",
                extra={"event_type": "user.password.change.unexpected_error"},
            )
            raise
