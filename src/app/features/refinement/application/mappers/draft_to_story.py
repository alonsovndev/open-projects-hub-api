"""
Maps a StoryDraftEntity to a StoryEntity for the approval workflow.

Extracted from approve_draft and approve_drafts_bulk to eliminate duplication.
"""

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority


def draft_to_story_entity(draft: StoryDraftEntity) -> StoryEntity:
    """
    Create a StoryEntity from an approved StoryDraftEntity.

    Merges description and acceptance criteria into a single structured
    description field on the story.

    Args:
        draft: The approved story draft

    Returns:
        A new StoryEntity ready to be persisted
    """
    description_parts: list[str] = []

    if draft.description:
        description_parts.append(draft.description)

    if draft.acceptance_criteria:
        description_parts.append("\n\n**Acceptance Criteria:**")
        for criterion in draft.acceptance_criteria:
            description_parts.append(f"- {criterion}")

    full_description = "\n".join(description_parts) if description_parts else None

    return StoryEntity.create(
        title=draft.title,
        project_id=draft.project_id,
        created_by=draft.created_by,
        description=full_description,
        priority=StoryPriority.MEDIUM,
        points=None,
    )
