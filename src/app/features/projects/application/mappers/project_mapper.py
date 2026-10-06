"""
Shared mapper for ProjectEntity to ProjectResponse.

Centralizes DTO mapping logic to reduce duplication across use cases.
"""

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.domain.entities.project_entity import ProjectEntity


def to_project_response(
    entity: ProjectEntity, client_name: str, stories_count: int = 0, completed_stories: int = 0
) -> ProjectResponse:
    """
    Convert ProjectEntity to ProjectResponse DTO.

    Args:
        entity: ProjectEntity domain object
        client_name: Name of the client (from joined query)
        stories_count: Total number of stories (optional)
        completed_stories: Number of completed stories (optional)

    Returns:
        ProjectResponse DTO with serialized entity data
    """
    return ProjectResponse(
        id=str(entity.id.value),
        name=entity.name,
        code=entity.code,
        access_code=entity.access_code,
        description=entity.description,
        created_by=str(entity.created_by.value),
        client_id=str(entity.client_id.value),
        client_name=client_name,
        status=entity.status.value,
        priority=entity.priority.value,
        phase=entity.phase.value,
        start_date=entity.start_date,
        end_date=entity.end_date,
        created_at=entity.created_at.isoformat(),
        updated_at=entity.updated_at.isoformat(),
        stories_count=stories_count,
        completed_stories=completed_stories,
    )
