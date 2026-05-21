"""Delete project use case."""
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId


class DeleteProjectUseCase:
    """Use case for deleting a project."""
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.
        
        Args:
            project_repository: Project repository
        """
        self._repository = project_repository
    
    async def execute(self, project_id: str) -> bool:
        """
        Execute delete project use case.
        
        Args:
            project_id: Project UUID string
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If project_id is invalid
        """
        # Parse and validate UUID
        entity_id = EntityId.from_string(project_id)
        
        return await self._repository.delete(entity_id.value)
