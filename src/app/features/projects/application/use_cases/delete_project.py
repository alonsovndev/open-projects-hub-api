"""Delete project use case."""

from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class DeleteProjectUseCase:
    """Use case for deleting a project."""

    def __init__(self, project_repository: ProjectRepository):
        self._repository = project_repository

    async def execute(self, project_id: str, ctx: RequestContext) -> None:
        """
        Delete a project. Raises ProjectNotFoundError if not found.

        Args:
            project_id: Project UUID string
            ctx: Caller identity and workspace

        Raises:
            ProjectNotFoundError: If project does not exist
            ValueError: If project_id is invalid
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        entity_id = EntityId.from_string(project_id)

        deleted = await self._repository.delete(entity_id.value, workspace_id=ctx.workspace_id.value)

        if not deleted:
            log.error(
                "Project not found for deletion",
                extra={"event_type": "project.delete.not_found", "entity_id": project_id},
            )
            raise ProjectNotFoundError(project_id)

        log.info("Project deleted", extra={"event_type": "project.deleted", "entity_id": project_id})
