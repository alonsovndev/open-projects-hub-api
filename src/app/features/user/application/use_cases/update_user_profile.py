"""
UpdateUserProfileUseCase - Update user profile (display_name only).

Only allows updating display_name. Email and role cannot be changed via this endpoint.
"""
from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.utils.log_util import log


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
                raise ValueError("Display name cannot be empty")
            
            if len(display_name) > 255:
                raise ValueError("Display name must not exceed 255 characters")
            
            # Find user
            user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))
            
            if user_entity is None:
                log.warning(f"User not found for profile update: {user_id}")
                raise UserNotFoundException(user_id)
            
            # Update display name (immutable entity pattern: create new instance)
            user_entity.display_name = display_name
            
            # Save updated entity
            updated_entity = await self.user_repository.save(user_entity)
            
            response = UserResponse(
                id=str(updated_entity.id.value),
                email=str(updated_entity.email.value),
                display_name=updated_entity.display_name,
                role=updated_entity.role.value
            )
            
            log.info(f"User profile updated: {user_id}")
            return response
            
        except (UserNotFoundException, ValueError):
            raise
        except Exception as e:
            log.error(f"Unexpected error in UpdateUserProfileUseCase: {str(e)}")
            raise
