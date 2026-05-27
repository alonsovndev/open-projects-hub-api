"""
ChangePasswordUseCase - Change user password with verification.

Requires current password verification before updating to new password.
"""

import re

from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.security.password_handler import PasswordHandler
from src.app.shared.logging import get_logger, log_business_event, log_error_event


log = get_logger(__name__)


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
            UserNotFoundException: If user doesn't exist
            ValueError: If validation fails or current password incorrect
        """
        try:
            # Validate new password
            self._validate_password(new_password)

            # Find user
            user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))

            if user_entity is None:
                log.warning(
                    "User not found for password change",
                    extra={
                        "user_id": user_id,
                        "event_type": "user.password.change.user_not_found",
                    },
                )
                raise UserNotFoundException(user_id)

            # Verify current password
            is_valid = await PasswordHandler.verify_password(current_password, user_entity.password_hash)

            if not is_valid:
                log.warning(
                    "Incorrect current password for password change",
                    extra={
                        "user_id": user_id,
                        "event_type": "user.password.change.incorrect_password",
                    },
                )
                raise ValueError("Current password is incorrect")

            # Hash new password
            new_password_hash = await PasswordHandler.hash_password(new_password)

            # Update password hash
            user_entity.password_hash = new_password_hash

            # Save updated entity
            await self.user_repository.save(user_entity)

            log_business_event(
                logger=log,
                event_type="user.password.changed",
                message="Password changed successfully",
                user_id=user_id,
            )

        except (UserNotFoundException, ValueError):
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="user.password.change.unexpected_error",
                message="Unexpected error during password change",
                error=e,
                user_id=user_id,
            )
            raise

    def _validate_password(self, password: str) -> None:
        """
        Validate password complexity requirements.

        Args:
            password: Password to validate

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[a-zA-Z]", password):
            raise ValueError("Password must contain at least one letter")

        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
