"""
Shared mapper for refinement DTOs.

Centralizes DTO mapping logic to reduce duplication across use cases.
"""

from src.app.features.refinement.application.dtos.refinement_dto import GeneratedStoryResponse
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
