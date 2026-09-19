"""Archive project use case."""

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.mappers.project_mapper import to_project_response
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class ArchiveProjectUseCase:
    """Use case for archiving an active or completed project."""

    def __init__(self, project_repository: ProjectRepository):
        self._repository = project_repository

    async def execute(self, project_id: str, created_by: str) -> ProjectResponse:
        """
        Archive a project, making it inactive.

        Args:
            project_id: Project UUID string
            created_by: User ID performing the action

        Returns:
            ProjectResponse with updated project data

        Raises:
            ProjectNotFoundError: If project is not found
        """
        log = get_logger(__name__)
        set_user_id(created_by)

        entity_id = EntityId.from_string(project_id)
        result = await self._repository.find_by_id(entity_id.value)

        if not result:
            log.error(
                "Project not found for archival",
                extra={"event_type": "project.archive.not_found", "entity_id": project_id},
            )
            raise ProjectNotFoundError(project_id)

        entity, client_name = result
        entity.archive()

        updated_entity = await self._repository.save(entity)
        total_stories, completed_stories = await self._repository.get_story_counts(entity_id.value)

        log.info(
            "Project archived",
            extra={"event_type": "project.archived", "entity_id": project_id},
        )

        return to_project_response(updated_entity, client_name, total_stories, completed_stories)
