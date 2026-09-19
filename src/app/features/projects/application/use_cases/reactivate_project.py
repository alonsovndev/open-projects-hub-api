"""Reactivate project use case."""

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.mappers.project_mapper import to_project_response
from src.app.features.projects.domain.exceptions.project_exceptions import (
    ActiveProjectLimitExceededError,
    ProjectNotFoundError,
)
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class ReactivateProjectUseCase:
    """Use case for reactivating an archived or completed project."""

    def __init__(self, project_repository: ProjectRepository, max_active_projects: int = 3):
        self._repository = project_repository
        self._max_active_projects = max_active_projects

    async def execute(self, project_id: str, created_by: str) -> ProjectResponse:
        """
        Reactivate an archived or completed project, making it active again.

        Subject to active-project limit enforcement.

        Args:
            project_id: Project UUID string
            created_by: User ID performing the action

        Returns:
            ProjectResponse with updated project data

        Raises:
            ProjectNotFoundError: If project is not found
            ActiveProjectLimitExceededError: If admin is at the active project limit
        """
        log = get_logger(__name__)
        set_user_id(created_by)

        entity_id = EntityId.from_string(project_id)
        result = await self._repository.find_by_id(entity_id.value)

        if not result:
            log.error(
                "Project not found for reactivation",
                extra={"event_type": "project.reactivate.not_found", "entity_id": project_id},
            )
            raise ProjectNotFoundError(project_id)

        entity, client_name = result

        # Enforce active project limit only when the project is not already active
        if entity.status.value != "active":
            created_by_id = EntityId.from_string(created_by)
            active_count = await self._repository.count_active_by_user(created_by_id.value)
            if active_count >= self._max_active_projects:
                log.warning(
                    "Active project limit reached on reactivation",
                    extra={
                        "event_type": "project.reactivate.limit_exceeded",
                        "user_id": created_by,
                        "active_count": active_count,
                        "limit": self._max_active_projects,
                    },
                )
                raise ActiveProjectLimitExceededError(self._max_active_projects)

        entity.reactivate()

        updated_entity = await self._repository.save(entity)
        total_stories, completed_stories = await self._repository.get_story_counts(entity_id.value)

        log.info(
            "Project reactivated",
            extra={"event_type": "project.reactivated", "entity_id": project_id},
        )

        return to_project_response(updated_entity, client_name, total_stories, completed_stories)
