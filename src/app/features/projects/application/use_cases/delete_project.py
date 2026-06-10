"""Delete project use case."""

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import BusinessLogger, get_logger


class DeleteProjectUseCase:
    """Use case for deleting a project."""

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.

        Args:
            project_repository: Project repository
        """
        self._repository = project_repository

    async def execute(self, project_id: str, created_by: str) -> bool:
        """
        Execute delete project use case.

        Args:
            project_id: Project UUID string
            created_by: User ID performing the deletion

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If project_id is invalid
        """
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        # Parse and validate UUID
        entity_id = EntityId.from_string(project_id)

        deleted = await self._repository.delete(entity_id.value)

        if deleted:
            log.event("project.deleted", entity_id=project_id)
        else:
            log.failure("project.delete.not_found", entity_id=project_id)

        return deleted
