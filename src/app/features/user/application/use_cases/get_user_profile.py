"""
GetUserProfileUseCase - Retrieve current user profile.

Returns user details (email, display_name, role) for authenticated user.
"""

from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.mappers.user_dto_mapper import to_user_response
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


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
            UserNotFoundError: If user doesn't exist
        """
        log = get_logger(__name__)
        set_user_id(user_id)

        try:
            user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))

            if user_entity is None:
                log.error(
                    "User profile not found", extra={"event_type": "user.profile.not_found", "entity_id": user_id}
                )
                raise UserNotFoundError(user_id)

            response = to_user_response(user_entity)

            log.info("User profile retrieved", extra={"event_type": "user.profile.retrieved", "entity_id": user_id})
            return response

        except UserNotFoundError:
            raise
        except Exception:
            log.exception(
                "Unexpected error retrieving user profile",
                extra={"event_type": "user.profile.unexpected_error", "entity_id": user_id},
            )
            raise
