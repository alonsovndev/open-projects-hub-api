from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class DeleteUserUseCase:
    """
    Lets a workspace Admin permanently delete a teammate.

    The projects and stories the person created, and the stories assigned to them, move to
    the Admin who deletes them. Their stored AI keys and pending email codes are erased.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, ctx: RequestContext) -> None:
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        target_user = await self.user_repository.find_by_id(EntityId.from_string(user_id))

        # Users of other workspaces answer 404 so their ids cannot be confirmed.
        if target_user is None or not target_user.belongs_to(ctx.workspace_id):
            log.warning("User not found for deletion", extra={"event_type": "user.delete.not_found"})
            raise UserNotFoundError(user_id)

        if target_user.is_admin():
            raise ValueError("The workspace Admin cannot be deleted")

        if not await self.user_repository.delete_handing_over(target_user.id, successor_id=ctx.user_id):
            raise UserNotFoundError(user_id)

        log.info("User deleted", extra={"event_type": "user.deleted", "target_user_id": user_id})
