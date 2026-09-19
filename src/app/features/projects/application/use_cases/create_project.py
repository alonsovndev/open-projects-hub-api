"""Create project use case."""

from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.projects.application.dtos.project_dto import CreateProjectRequest, ProjectResponse
from src.app.features.projects.application.mappers.project_mapper import to_project_response
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ActiveProjectLimitExceededError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.domain.value_objects.project_phase import ProjectPhase
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class CreateProjectUseCase:
    """Use case for creating a new project."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        client_repository: ClientRepository,
        max_active_projects: int = 3,
    ):
        self._project_repository = project_repository
        self._client_repository = client_repository
        self._max_active_projects = max_active_projects

    async def execute(self, request: CreateProjectRequest, created_by: str) -> ProjectResponse:
        """
        Execute create project use case.

        Args:
            request: CreateProjectRequest DTO with project data
            created_by: User ID of creator (from JWT token)

        Returns:
            ProjectResponse with created project data

        Raises:
            ActiveProjectLimitExceededError: If admin is at the active project limit
            NotFoundError: If client is not found
            RuntimeError: If save fails unexpectedly
        """
        log = get_logger(__name__)
        set_user_id(created_by)

        created_by_id = EntityId.from_string(created_by)

        # Enforce active project limit before creating
        active_count = await self._project_repository.count_active_by_user(created_by_id.value)
        if active_count >= self._max_active_projects:
            log.warning(
                "Active project limit reached",
                extra={
                    "event_type": "project.create.limit_exceeded",
                    "user_id": created_by,
                    "active_count": active_count,
                    "limit": self._max_active_projects,
                },
            )
            raise ActiveProjectLimitExceededError(self._max_active_projects)

        # Ensure client exists before creating project to maintain referential integrity
        client_entity_id = EntityId.from_string(request.client_id)
        client = await self._client_repository.find_by_id(client_entity_id.value)
        if not client:
            log.error(
                "Client not found for project creation",
                extra={"event_type": "project.create.client_not_found", "client_id": request.client_id},
            )
            raise NotFoundError("Client", request.client_id)

        priority_enum = ProjectPriority(request.priority) if request.priority else ProjectPriority.default()
        phase_enum = ProjectPhase(request.phase)

        entity = ProjectEntity.create(
            name=request.name,
            code=request.code,
            created_by=created_by_id,
            client_id=client_entity_id,
            description=request.description,
            priority=priority_enum,
            start_date=request.start_date,
            end_date=request.end_date,
            phase=phase_enum,
        )

        saved_entity = await self._project_repository.save(entity)

        if not saved_entity:
            log.error(
                "Failed to save project",
                extra={
                    "event_type": "project.create.save_failed",
                    "project_name": request.name,
                    "project_code": request.code,
                },
            )
            raise RuntimeError("Failed to create project")

        log.info(
            "Project created",
            extra={
                "event_type": "project.created",
                "entity_id": str(saved_entity.id),
                "project_name": saved_entity.name,
                "project_code": saved_entity.code,
                "client_id": str(saved_entity.client_id),
                "client_name": client.name,
                "priority": saved_entity.priority.value,
            },
        )

        # New project always starts with zero stories
        return to_project_response(saved_entity, client.name, stories_count=0, completed_stories=0)
