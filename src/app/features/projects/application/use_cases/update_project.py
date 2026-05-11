"""Update project use case."""
from datetime import date
from typing import Optional

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.infrastructure.mappers.project_mapper import to_project_response


class UpdateProjectUseCase:
    """Use case for updating a project."""
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.
        
        Args:
            project_repository: Project repository
        """
        self._repository = project_repository
    
    async def execute(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[ProjectResponse]:
        """
        Execute update project use case.
        
        Args:
            project_id: Project UUID string
            name: Optional new name
            description: Optional new description
            status: Optional new status
            start_date: Optional new start date
            end_date: Optional new end date
            
        Returns:
            ProjectResponse if updated, None if not found
            
        Raises:
            ValueError: If validation fails
        """
        # Parse and validate UUID
        entity_id = EntityId.from_string(project_id)
        
        # Fetch existing project
        entity = await self._repository.find_by_id(entity_id.value)
        
        if not entity:
            return None
        
        # Convert status string to enum if provided
        status_enum = None
        if status is not None:
            status_enum = ProjectStatus(status)
        
        # Update entity
        entity.update_details(
            name=name,
            description=description,
            status=status_enum,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Save updated entity
        updated_entity = await self._repository.save(entity)
        
        if not updated_entity:
            raise ValueError("Failed to update project")
        
        # Return DTO using shared mapper
        return to_project_response(updated_entity)
