"""
UpdateUserProfileUseCase - Update user profile (display_name only).

Only allows updating display_name. Email and role cannot be changed via this endpoint.
"""

from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, log_business_event, log_error_event, mask_email


log = get_logger(__name__)


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
            UserNotFoundException: If user doesn't exist
            ValueError: If validation fails
        """
        try:
            # Validate display name
            if not display_name or display_name.strip() == "":
                log.warning(
                    "Empty display name validation failed",
                    extra={
                        "user_id": user_id,
                        "event_type": "user.profile.update.validation_failed",
                    },
                )
                raise ValueError("Display name cannot be empty")

            if len(display_name) > 255:
                log.warning(
                    "Display name exceeds max length",
                    extra={
                        "user_id": user_id,
                        "display_name_length": len(display_name),
                        "event_type": "user.profile.update.validation_failed",
                    },
                )
                raise ValueError("Display name must not exceed 255 characters")

            # Find user
            user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))

            if user_entity is None:
                log.warning(
                    "User not found for profile update",
                    extra={
                        "user_id": user_id,
                        "event_type": "user.profile.update.user_not_found",
                    },
                )
                raise UserNotFoundException(user_id)

            old_display_name = user_entity.display_name

            # Update display name (immutable entity pattern: create new instance)
            user_entity.display_name = display_name

            # Save updated entity
            updated_entity = await self.user_repository.update(user_entity)

            if updated_entity is None:
                log_error_event(
                    logger=log,
                    error_type="user.profile.update.save_failed",
                    message="Failed to update user profile",
                    user_id=user_id,
                )
                raise ValueError("Failed to update user profile")

            response = UserResponse(
                id=str(updated_entity.id.value),
                email=str(updated_entity.email.value),
                display_name=updated_entity.display_name,
                role=updated_entity.role.value,
            )

            log_business_event(
                logger=log,
                event_type="user.profile.updated",
                message="User profile updated successfully",
                user_id=user_id,
                additional_data={
                    "email": mask_email(str(updated_entity.email.value)),
                    "old_display_name": old_display_name,
                    "new_display_name": display_name,
                },
            )
            return response

        except (UserNotFoundException, ValueError):
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="user.profile.update.unexpected_error",
                message="Unexpected error during profile update",
                error=e,
                user_id=user_id,
            )
            raise
