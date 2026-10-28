"""
UpdateUserOnboardingUseCase - Dismiss or replay the first-use welcome (F-005).
"""

from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.mappers.user_dto_mapper import to_user_response
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class UpdateUserOnboardingUseCase:
    """Marks the caller's onboarding as completed, or clears it so it shows again."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, completed: bool) -> UserResponse:
        """
        Args:
            user_id: UUID string of the user (extracted from JWT)
            completed: True to dismiss onboarding, False to show it again

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        log = get_logger(__name__)
        set_user_id(user_id)

        user_entity = await self.user_repository.find_by_id(EntityId.from_string(user_id))
        if user_entity is None:
            raise UserNotFoundError(user_id)

        if completed:
            user_entity.complete_onboarding()
        else:
            user_entity.reset_onboarding()

        updated_entity = await self.user_repository.update(user_entity)
        if updated_entity is None:
            raise UserNotFoundError(user_id)

        log.info(
            "User onboarding updated",
            extra={"event_type": "user.onboarding.updated", "completed": completed},
        )
        return to_user_response(updated_entity)
