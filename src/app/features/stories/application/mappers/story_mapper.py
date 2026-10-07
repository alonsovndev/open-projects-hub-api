"""
Shared mapper for StoryEntity to StoryResponse.

Centralizes DTO mapping logic to reduce duplication across use cases.
"""

from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.features.stories.domain.entities.story_entity import StoryEntity


def to_story_response(entity: StoryEntity) -> StoryResponse:
    """
    Convert StoryEntity to StoryResponse DTO.

    Args:
        entity: StoryEntity domain object

    Returns:
        StoryResponse DTO with serialized entity data
    """
    return StoryResponse(
        id=str(entity.id.value),
        title=entity.title,
        description=entity.description,
        acceptance_criteria=entity.acceptance_criteria,
        project_id=str(entity.project_id.value),
        created_by=str(entity.created_by.value),
        assigned_to=str(entity.assigned_to.value) if entity.assigned_to else None,
        status=entity.status.value,
        priority=entity.priority.value,
        points=entity.points,
        created_at=entity.created_at.isoformat(),
        updated_at=entity.updated_at.isoformat(),
    )
