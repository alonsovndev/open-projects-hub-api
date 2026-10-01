"""
Shared mapper for refinement DTOs.

Centralizes DTO mapping logic to reduce duplication across use cases.
"""

from src.app.features.refinement.application.dtos.refinement_dto import GeneratedStoryResponse
from src.app.features.refinement.infrastructure.ai.ai_service import GeneratedStory


def to_generated_story_response(generated_story: GeneratedStory) -> GeneratedStoryResponse:
    """Convert GeneratedStory from the AI service to its response DTO."""
    return GeneratedStoryResponse(
        title=generated_story.title,
        description=generated_story.description,
        acceptance_criteria=generated_story.acceptance_criteria,
    )
