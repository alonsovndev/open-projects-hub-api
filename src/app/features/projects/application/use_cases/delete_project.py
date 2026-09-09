"""Delete project use case."""

from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


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
        log = get_logger(__name__)
        set_user_id(created_by)

        # Parse and validate UUID
        entity_id = EntityId.from_string(project_id)

        deleted = await self._repository.delete(entity_id.value)

        if deleted:
            log.info("Project deleted", extra={"event_type": "project.deleted", "entity_id": project_id})
        else:
            log.error(
                "Project not found for deletion",
                extra={"event_type": "project.delete.not_found", "entity_id": project_id},
            )

        return deleted
