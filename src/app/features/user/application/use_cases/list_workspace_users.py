from src.app.features.user.application.dtos.user_dto import UserResponse
from src.app.features.user.application.mappers.user_dto_mapper import to_user_response
from src.app.features.user.domain.repositories.user_repository import UserRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.logging import set_user_id


class ListWorkspaceUsersUseCase:
    """The caller's teammates and viewers, for the Team settings page and assignee pickers."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, ctx: RequestContext, limit: int, offset: int) -> list[UserResponse]:
        set_user_id(str(ctx.user_id))
        users = await self.user_repository.find_all(ctx.workspace_id, limit=limit, offset=offset)
        return [to_user_response(user) for user in users]
