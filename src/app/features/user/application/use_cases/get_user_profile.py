"""
GetUserProfileUseCase - Retrieve current user profile.

Returns user details (email, display_name, role) for authenticated user.
"""
from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.exceptions.user_exception import UserNotFoundException
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.utils.log_util import log


class GetUserProfileUseCase:
    """
    Use case for retrieving user profile.
    
    Fetches user details for authenticated user from JWT token.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str) -> UserResponse:
        """
        Get user profile by user ID.
        
        Args:
            user_id: UUID string of the user (extracted from JWT)
            
        Returns:
            UserResponse with user profile data
            
        Raises:
            UserNotFoundException: If user doesn't exist
        """
        try:
            user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))
            
            if user_entity is None:
                log.warning(f"User profile not found: {user_id}")
                raise UserNotFoundException(user_id)
            
            response = UserResponse(
                id=str(user_entity.id.value),
                email=str(user_entity.email.value),
                display_name=user_entity.display_name,
                role=user_entity.role.value
            )
            
            log.info(f"User profile retrieved: {user_id}")
            return response
            
        except UserNotFoundException:
            raise
        except Exception as e:
            log.error(f"Unexpected error in GetUserProfileUseCase: {str(e)}")
            raise
