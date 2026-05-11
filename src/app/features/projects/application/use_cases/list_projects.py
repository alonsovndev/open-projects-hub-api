"""List projects use case."""
from typing import List, Optional

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.infrastructure.mappers.project_mapper import to_project_response


class ListProjectsUseCase:
    """Use case for listing projects with pagination."""
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.
        
        Args:
            project_repository: Project repository
        """
        self._repository = project_repository
    
    async def execute(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[ProjectResponse]:
        """
        Execute list projects use case.
        
        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)
            
        Returns:
            List of ProjectResponse objects
        """
        # Fetch from repository
        entities = await self._repository.find_all(
            limit=limit,
            offset=offset,
            status=status,
        )
        
        # Convert to DTOs using shared mapper
        return [to_project_response(entity) for entity in entities]
