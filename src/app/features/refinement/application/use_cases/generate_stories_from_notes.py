"""Generate multiple stories from raw discovery notes use case."""
from typing import List

from src.app.features.refinement.application.dtos.refinement_dto import (
    GeneratedStoryResponse,
    GenerateStoriesRequest,
    GenerateStoriesResponse,
)
from src.app.features.refinement.application.mappers.story_draft_mapper import to_generated_story_response
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.domain.value_objects.refinement_status import RefinementStatus
from src.app.features.refinement.infrastructure.ai.ai_service import AIService, AIServiceError
from src.app.shared.domain.value_objects.entity_id import EntityId


class GenerateStoriesFromNotesUseCase:
    """Use case for generating multiple story drafts from raw notes using AI."""
    
    def __init__(
        self,
        repository: StoryDraftRepository,
        ai_service: AIService,
    ):
        """
        Initialize use case.
        
        Args:
            repository: Story draft repository
            ai_service: AI service for story generation
        """
        self._repository = repository
        self._ai_service = ai_service
    
    async def execute(
        self,
        request: GenerateStoriesRequest,
        created_by: str,
    ) -> GenerateStoriesResponse:
        """
        Execute bulk story generation from raw notes.
        
        Args:
            request: GenerateStoriesRequest with project_id and raw_notes
            created_by: User UUID string who created the drafts
            
        Returns:
            GenerateStoriesResponse with generated stories
            
        Raises:
            AIServiceError: If AI service fails
        """
        result = await self._ai_service.generate_stories_from_notes(request.raw_notes)
        
        project_uuid = EntityId.from_string(request.project_id)
        creator_uuid = EntityId.from_string(created_by)
        
        story_responses: List[GeneratedStoryResponse] = []
        
        for generated_story in result.stories:
            draft = StoryDraftEntity.create(
                title=generated_story.title,
                description=generated_story.description,
                acceptance_criteria=generated_story.acceptance_criteria,
                project_id=project_uuid,
                created_by=creator_uuid,
            )
            
            saved_draft = await self._repository.save(draft)
            
            story_responses.append(
                to_generated_story_response(
                    draft_id=str(saved_draft.id.value),
                    generated_story=generated_story,
                )
            )
        
        return GenerateStoriesResponse(
            stories=story_responses,
            raw_notes=request.raw_notes,
        )
