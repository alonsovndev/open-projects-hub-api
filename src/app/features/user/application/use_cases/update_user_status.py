from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.mappers.user_dto_mapper import to_user_response
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class UpdateUserStatusUseCase:
    """
    Lets a workspace Admin switch a teammate between active and inactive.

    An inactive account keeps its data and stays in the team list but cannot sign in or
    refresh a session, and cannot be assigned stories. An access token already issued works
    until it expires. Turning the account back on lets the person sign in again.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, active: bool, ctx: RequestContext) -> UserResponse:
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        target_user = await self.user_repository.find_by_id(EntityId.from_string(user_id))

        # Users of other workspaces answer 404 so their ids cannot be confirmed.
        if target_user is None or not target_user.belongs_to(ctx.workspace_id):
            log.warning("User not found for status update", extra={"event_type": "user.status.update.not_found"})
            raise UserNotFoundError(user_id)

        if target_user.is_admin():
            raise ValueError("The workspace Admin cannot be deactivated")

        if active == target_user.is_active:
            return to_user_response(target_user)

        if active:
            target_user.activate()
        else:
            target_user.deactivate()

        updated_user = await self.user_repository.update(target_user)
        if updated_user is None:
            raise ValueError("Failed to update user status")

        log.info(
            "User status updated",
            extra={"event_type": "user.status.updated", "target_user_id": user_id, "active": active},
        )
        return to_user_response(updated_user)
