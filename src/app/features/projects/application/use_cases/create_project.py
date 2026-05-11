"""Create project use case."""
from datetime import date
from typing import Optional

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.mappers.project_mapper import to_project_response


class CreateProjectUseCase:
    """Use case for creating a new project."""
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.
        
        Args:
            project_repository: Project repository
        """
        self._repository = project_repository
    
    async def execute(
        self,
        name: str,
        created_by: str,
        description: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ProjectResponse:
        """
        Execute create project use case.
        
        Args:
            name: Project name
            created_by: User ID of creator
            description: Optional description
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            ProjectResponse with created project data
            
        Raises:
            ValueError: If validation fails
        """
        # Create entity
        entity = ProjectEntity.create(
            name=name,
            created_by=EntityId.from_string(created_by),
            description=description,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Save to repository
        saved_entity = await self._repository.save(entity)
        
        if not saved_entity:
            raise ValueError("Failed to create project")
        
        # Return DTO using shared mapper
        return to_project_response(saved_entity)
