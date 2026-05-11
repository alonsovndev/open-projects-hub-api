"""
Shared mapper for ProjectEntity to ProjectResponse.

Centralizes DTO mapping logic to reduce duplication across use cases.
"""
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.application.dtos.project_dto import ProjectResponse


def to_project_response(entity: ProjectEntity) -> ProjectResponse:
    """
    Convert ProjectEntity to ProjectResponse DTO.
    
    Args:
        entity: ProjectEntity domain object
        
    Returns:
        ProjectResponse DTO with serialized entity data
    """
    return ProjectResponse(
        id=str(entity.id.value),
        name=entity.name,
        description=entity.description,
        created_by=str(entity.created_by.value),
        status=entity.status.value,
        start_date=entity.start_date,
        end_date=entity.end_date,
        created_at=entity.created_at.isoformat(),
        updated_at=entity.updated_at.isoformat(),
    )
