"""Create project use case."""
from src.app.features.projects.application.dtos.project_dto import (
    CreateProjectRequest,
    ProjectResponse,
)
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.features.projects.application.mappers.project_mapper import to_project_response


class CreateProjectUseCase:
    """Use case for creating a new project."""
    
    def __init__(self, project_repository: ProjectRepository, client_repository: ClientRepository):
        """
        Initialize use case.
        
        Args:
            project_repository: Project repository
            client_repository: Client repository
        """
        self._project_repository = project_repository
        self._client_repository = client_repository
    
    async def execute(self, request: CreateProjectRequest, created_by: str) -> ProjectResponse:
        """
        Execute create project use case.
        
        Args:
            request: CreateProjectRequest DTO with project data
            created_by: User ID of creator (from JWT token)
            
        Returns:
            ProjectResponse with created project data
            
        Raises:
            ValueError: If validation fails or client not found
        """
        # Ensure client exists before creating project to maintain referential integrity
        client_entity_id = EntityId.from_string(request.client_id)
        client = await self._client_repository.find_by_id(client_entity_id.value)
        if not client:
            raise ValueError(f"Client not found: {request.client_id}")
        
        priority_enum = ProjectPriority(request.priority) if request.priority else ProjectPriority.default()
        
        entity = ProjectEntity.create(
            name=request.name,
            code=request.code,
            created_by=EntityId.from_string(created_by),
            client_id=client_entity_id,
            description=request.description,
            priority=priority_enum,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        saved_entity = await self._project_repository.save(entity)
        
        if not saved_entity:
            raise ValueError("Failed to create project")
        
        # New project always starts with zero stories
        return to_project_response(saved_entity, client.name, stories_count=0, completed_stories=0)
