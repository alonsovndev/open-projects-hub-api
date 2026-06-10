"""Get project by ID use case."""

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.mappers.project_mapper import to_project_response
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import BusinessLogger, get_logger


class GetProjectByIdUseCase:
    """Use case for getting a project by ID."""

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.

        Args:
            project_repository: Project repository
        """
        self._repository = project_repository

    async def execute(self, project_id: str, user_id: str) -> ProjectResponse | None:
        """
        Execute get project by ID use case.

        Args:
            project_id: Project UUID string
            user_id: Current user ID

        Returns:
            ProjectResponse if found, None otherwise

        Raises:
            ValueError: If project_id is invalid
        """
        log = BusinessLogger(get_logger(__name__), user_id=user_id)

        log.info("Fetching project by ID", event_type="projects.fetch_by_id.started", project_id=project_id)
        entity_id = EntityId.from_string(project_id)

        result = await self._repository.find_by_id(entity_id.value)

        if not result:
            log.warning("Project not found", event_type="projects.fetch_by_id.not_found", project_id=project_id)
            return None

        entity, client_name = result

        total_stories, completed_stories = await self._repository.get_story_counts(entity_id.value)

        log.event("projects.fetch_by_id.success", project_id=project_id)
        return to_project_response(entity, client_name, total_stories, completed_stories)
