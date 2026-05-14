"""List projects use case."""
from typing import Optional

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
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
    ) -> PaginatedResponse[ProjectResponse]:
        """
        Execute list projects use case.
        
        Args:
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)
            
        Returns:
            PaginatedResponse containing pagination metadata and ProjectResponse items
        """
        # Fetch total count and items from repository
        total = await self._repository.count(status=status)
        entities = await self._repository.find_all(
            limit=limit,
            offset=offset,
            status=status,
        )
        
        # Convert to DTOs using shared mapper
        items = [to_project_response(entity) for entity in entities]
        
        # Calculate page number (1-indexed)
        page = (offset // limit) + 1 if limit > 0 else 1
        
        return PaginatedResponse(
            total=total,
            page=page,
            per_page=limit,
            items=items,
        )
