"""Maps story entities to their backlog-view representation."""

from src.app.features.backlog.application.dtos.backlog_dto import BacklogStoryResponse
from src.app.features.stories.domain.entities.story_entity import StoryEntity


def to_backlog_story_response(entity: StoryEntity) -> BacklogStoryResponse:
    """
    Convert a StoryEntity to its backlog representation.

    Narrower than StoryResponse on purpose: the backlog is a stakeholder-facing view, so it
    leaves out the internal assignment and authorship fields.

    Args:
        entity: StoryEntity domain object

    Returns:
        BacklogStoryResponse DTO
    """
    return BacklogStoryResponse(
        id=str(entity.id.value),
        title=entity.title,
        description=entity.description,
        acceptance_criteria=entity.acceptance_criteria,
        status=entity.status.value,
        priority=entity.priority.value,
        points=entity.points,
        created_at=entity.created_at.isoformat(),
        updated_at=entity.updated_at.isoformat(),
    )
