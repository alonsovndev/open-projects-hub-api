from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.mappers.user_dto_mapper import to_user_response
from src.app.features.user.domain.exceptions.user_exceptions import UserNotFoundError
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class UpdateUserRoleUseCase:
    """
    Lets a workspace Admin switch a teammate between member and viewer.

    The role is embedded in access tokens, so sessions are revoked: the person's next
    refresh fails and signing in again issues tokens with the new role.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: str, role: str, ctx: RequestContext) -> UserResponse:
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        target_user = await self.user_repository.find_by_id(EntityId.from_string(user_id))

        # Users of other workspaces answer 404 so their ids cannot be confirmed.
        if target_user is None or not target_user.belongs_to(ctx.workspace_id):
            log.warning("User not found for role update", extra={"event_type": "user.role.update.not_found"})
            raise UserNotFoundError(user_id)

        if target_user.is_admin():
            raise ValueError("The workspace Admin's role cannot be changed")

        target_user.update_details(role=UserRole(role))
        target_user.revoke_sessions()

        updated_user = await self.user_repository.update(target_user)
        if updated_user is None:
            raise ValueError("Failed to update user role")

        log.info(
            "User role updated",
            extra={"event_type": "user.role.updated", "target_user_id": user_id, "new_role": role},
        )
        return to_user_response(updated_user)
