"""
Shared mapper for refinement DTOs.

Centralizes DTO mapping logic to reduce duplication across use cases.
"""

from src.app.features.refinement.application.dtos.refinement_dto import GeneratedStoryResponse, StoryDraftResponse
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.infrastructure.ai.ai_service import GeneratedStory


def to_generated_story_response(
    draft_id: str,
    generated_story: GeneratedStory,
) -> GeneratedStoryResponse:
    """
    Convert GeneratedStory to GeneratedStoryResponse DTO.

    Args:
        draft_id: Saved draft ID
        generated_story: GeneratedStory from AI service

    Returns:
        GeneratedStoryResponse DTO
    """
    return GeneratedStoryResponse(
        id=draft_id,
        title=generated_story.title,
        description=generated_story.description,
        acceptance_criteria=generated_story.acceptance_criteria,
    )


def to_story_draft_response(draft: StoryDraftEntity) -> StoryDraftResponse:
    """
    Convert a StoryDraftEntity to its API response DTO.

    Args:
        draft: Persisted story draft

    Returns:
        StoryDraftResponse DTO
    """
    return StoryDraftResponse(
        id=str(draft.id.value),
        project_id=str(draft.project_id.value),
        title=draft.title,
        description=draft.description,
        acceptance_criteria=draft.acceptance_criteria,
        status=draft.status.value,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )
