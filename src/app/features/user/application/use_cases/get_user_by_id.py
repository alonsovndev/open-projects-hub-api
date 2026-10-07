from src.app.features.user.application.mappers.user_dto_mapper import UserResponse, to_user_response
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class GetUserByIdUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, ctx: RequestContext) -> UserResponse:
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        user_obj_id = EntityId.from_string(user_id)
        existing_user = await self.user_repository.find_by_id(user_obj_id)

        if not existing_user or not existing_user.belongs_to(ctx.workspace_id):
            log.error("User not found", extra={"event_type": "user.not_found", "entity_id": user_id})
            raise UserNotFoundError(user_id)

        return to_user_response(existing_user)
