"""Update project use case."""

from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.projects.application.dtos.project_dto import ProjectResponse, UpdateProjectRequest
from src.app.features.projects.application.mappers.project_mapper import to_project_response
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.logging import get_logger, set_user_id


class UpdateProjectUseCase:
    """Use case for updating a project."""

    def __init__(self, project_repository: ProjectRepository, client_repository: ClientRepository):
        """
        Initialize use case.

        Args:
            project_repository: Project repository
            client_repository: Client repository
        """
        self._project_repository = project_repository
        self._client_repository = client_repository

    async def execute(self, project_id: str, request: UpdateProjectRequest, created_by: str) -> ProjectResponse:
        """
        Execute update project use case.

        Args:
            project_id: Project UUID string
            request: UpdateProjectRequest DTO with fields to update
            created_by: User ID performing the update

        Returns:
            ProjectResponse if updated

        Raises:
            ProjectNotFoundError: If project is not found
            NotFoundError: If client is not found
            RuntimeError: If save fails unexpectedly
        """
        log = get_logger(__name__)
        set_user_id(created_by)

        # Parse and validate UUID
        entity_id = EntityId.from_string(project_id)

        result = await self._project_repository.find_by_id(entity_id.value)

        if not result:
            log.error(
                "Project not found for update",
                extra={"event_type": "project.update.not_found", "entity_id": project_id},
            )
            raise ProjectNotFoundError(project_id)

        entity, old_client_name = result
        client_name = old_client_name

        # Verify new client exists when changing project's client association
        client_entity_id = None
        if request.client_id is not None:
            client_entity_id = EntityId.from_string(request.client_id)
            client = await self._client_repository.find_by_id(client_entity_id.value)
            if not client:
                log.error(
                    "Client not found for project update",
                    extra={"event_type": "project.update.client_not_found", "client_id": request.client_id},
                )
                raise NotFoundError("Client", request.client_id)
            client_name = client.name

        status_enum = None
        if request.status is not None:
            status_enum = ProjectStatus(request.status)

        priority_enum = None
        if request.priority is not None:
            priority_enum = ProjectPriority(request.priority)

        entity.update_details(
            name=request.name,
            code=request.code,
            description=request.description,
            client_id=client_entity_id,
            status=status_enum,
            priority=priority_enum,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        updated_entity = await self._project_repository.save(entity)

        if not updated_entity:
            log.error(
                "Failed to save project update",
                extra={"event_type": "project.update.save_failed", "entity_id": project_id},
            )
            raise RuntimeError("Failed to update project")

        total_stories, completed_stories = await self._project_repository.get_story_counts(entity_id.value)

        log.info(
            "Project updated",
            extra={"event_type": "project.updated", "entity_id": project_id, "project_name": updated_entity.name},
        )

        return to_project_response(updated_entity, client_name, total_stories, completed_stories)
