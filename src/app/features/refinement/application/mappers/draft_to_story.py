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

    Acceptance criteria stay a list rather than being folded into the description: the
    backlog view and the Markdown export both need them structured, and text merged into
    a free-text field cannot be read back reliably once an Admin edits it.

    Args:
        draft: The approved story draft

    Returns:
        A new StoryEntity ready to be persisted
    """
    return StoryEntity.create(
        title=draft.title,
        project_id=draft.project_id,
        created_by=draft.created_by,
        description=draft.description,
        priority=StoryPriority.MEDIUM,
        points=None,
        acceptance_criteria=draft.acceptance_criteria,
    )
