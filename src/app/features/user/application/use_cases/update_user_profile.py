"""
UpdateUserProfileUseCase - Update user profile (display_name only).

Only allows updating display_name. Email and role cannot be changed via this endpoint.
"""

from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.mappers.user_dto_mapper import to_user_response
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.validators.user_validators import UserValidators
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import BusinessLogger, get_logger, mask_email


class UpdateUserProfileUseCase:
    """
    Use case for updating user profile.

    Only display_name can be updated. Email and role are immutable via this endpoint.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, display_name: str) -> UserResponse:
        """
        Update user profile (display_name only).

        Args:
            user_id: UUID string of the user (extracted from JWT)
            display_name: New display name (max 255 chars)

        Returns:
            UserResponse with updated profile data

        Raises:
            UserNotFoundError: If user doesn't exist
            ValueError: If validation fails
        """
        log = BusinessLogger(get_logger(__name__), user_id=user_id)

        try:
            # Validate display name
            UserValidators.validate_display_name(display_name)

            # Find user
            user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))

            if user_entity is None:
                log.warning(
                    "User not found for profile update",
                    event_type="user.profile.update.user_not_found",
                    user_id=user_id,
                )
                raise UserNotFoundError(user_id)

            old_display_name = user_entity.display_name

            # Update display name (immutable entity pattern: create new instance)
            user_entity.update_details(display_name=display_name)

            # Save updated entity
            updated_entity = await self.user_repository.update(user_entity)

            if updated_entity is None:
                log.failure("user.profile.update.save_failed")
                raise ValueError("Failed to update user profile")

            response = to_user_response(updated_entity)

            log.event(
                "user.profile.updated",
                email=mask_email(str(updated_entity.email.value)),
                old_display_name=old_display_name,
                new_display_name=display_name,
            )
            return response

        except (UserNotFoundError, ValueError):
            raise
        except Exception as e:
            log.failure("user.profile.update.unexpected_error", error=e)
            raise
