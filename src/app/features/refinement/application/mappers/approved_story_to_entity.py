"""Maps an approved refined story to a StoryEntity for the approval workflow."""

from src.app.features.refinement.application.dtos.refinement_dto import ApproveStoryRequest
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.shared.domain.value_objects.entity_id import EntityId


def approved_story_to_entity(request: ApproveStoryRequest, created_by: EntityId) -> StoryEntity:
    """
    Create a StoryEntity from a story the Admin approved.

    Acceptance criteria stay a list rather than being folded into the description: the
    backlog view and the Markdown export both need them structured, and text merged into
    a free-text field cannot be read back reliably once an Admin edits it.
    """
    return StoryEntity.create(
        title=request.title,
        project_id=EntityId.from_string(request.project_id),
        created_by=created_by,
        description=request.description,
        priority=StoryPriority.MEDIUM,
        points=None,
        acceptance_criteria=request.acceptance_criteria,
    )
