"""Get project by ID use case."""
from typing import Optional

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.mappers.project_mapper import to_project_response


class GetProjectByIdUseCase:
    """Use case for getting a project by ID."""
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.
        
        Args:
            project_repository: Project repository
        """
        self._repository = project_repository
    
    async def execute(self, project_id: str) -> Optional[ProjectResponse]:
        """
        Execute get project by ID use case.
        
        Args:
            project_id: Project UUID string
            
        Returns:
            ProjectResponse if found, None otherwise
            
        Raises:
            ValueError: If project_id is invalid
        """
        # Parse and validate UUID
        entity_id = EntityId.from_string(project_id)
        
        # Fetch from repository
        entity = await self._repository.find_by_id(entity_id.value)
        
        if not entity:
            return None
        
        # Return DTO using shared mapper
        return to_project_response(entity)
