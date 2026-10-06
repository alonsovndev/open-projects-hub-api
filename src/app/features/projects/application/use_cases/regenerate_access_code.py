"""Regenerate project access code use case."""

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.mappers.project_mapper import to_project_response
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class RegenerateAccessCodeUseCase:
    """Use case for replacing a project's access code, which revokes the old code and link."""

    def __init__(self, project_repository: ProjectRepository):
        self._repository = project_repository

    async def execute(self, project_id: str, ctx: RequestContext) -> ProjectResponse:
        """
        Replace the project's access code.

        Args:
            project_id: Project UUID string
            ctx: Caller identity and workspace

        Returns:
            ProjectResponse carrying the new access code

        Raises:
            ProjectNotFoundError: If the project is not in the caller's workspace
        """
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))
        workspace_id = ctx.workspace_id.value

        entity_id = EntityId.from_string(project_id)
        result = await self._repository.find_by_id(entity_id.value, workspace_id=workspace_id)

        if not result:
            raise ProjectNotFoundError(project_id)

        entity, client_name = result
        entity.regenerate_access_code()

        updated_entity = await self._repository.save(entity)
        total_stories, completed_stories = await self._repository.get_story_counts(
            entity_id.value, workspace_id=workspace_id
        )

        log.info(
            "Project access code regenerated",
            extra={"event_type": "project.access_code.regenerated", "entity_id": project_id},
        )

        return to_project_response(updated_entity, client_name, total_stories, completed_stories)
