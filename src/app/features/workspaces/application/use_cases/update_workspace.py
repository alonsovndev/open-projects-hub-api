"""Update workspace use case."""

from src.app.features.workspaces.application.dtos.workspace_dto import UpdateWorkspaceRequest, WorkspaceResponse
from src.app.features.workspaces.domain.exceptions.workspace_exceptions import WorkspaceNotFoundError
from src.app.features.workspaces.domain.repositories.workspace_repository import WorkspaceRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.logging import get_logger, set_user_id


class UpdateWorkspaceUseCase:
    """Use case for renaming the caller's workspace."""

    def __init__(self, workspace_repository: WorkspaceRepository):
        self.workspace_repository = workspace_repository

    async def execute(self, request: UpdateWorkspaceRequest, ctx: RequestContext) -> WorkspaceResponse:
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        try:
            workspace = await self.workspace_repository.find_by_id(ctx.workspace_id)
            if workspace is None:
                log.error(
                    "Workspace not found for update",
                    extra={"event_type": "workspace.update.not_found", "entity_id": str(ctx.workspace_id.value)},
                )
                raise WorkspaceNotFoundError(str(ctx.workspace_id.value))

            previous_name = workspace.name
            workspace.rename(request.name)
            updated_workspace = await self.workspace_repository.update(workspace)

            log.info(
                "Workspace renamed",
                extra={
                    "event_type": "workspace.updated",
                    "entity_id": str(ctx.workspace_id.value),
                    "changes": {"name": {"old": previous_name, "new": updated_workspace.name}},
                },
            )
            return WorkspaceResponse(id=str(updated_workspace.id.value), name=updated_workspace.name)

        except (WorkspaceNotFoundError, ValueError):
            raise
        except Exception:
            log.exception(
                "Unexpected error updating workspace",
                extra={"event_type": "workspace.update.unexpected_error", "entity_id": str(ctx.workspace_id.value)},
            )
            raise
