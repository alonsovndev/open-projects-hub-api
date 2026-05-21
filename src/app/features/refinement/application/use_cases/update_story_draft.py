"""Update story draft use case."""
from typing import Optional

from src.app.features.refinement.application.dtos.refinement_dto import UpdateStoryDraftRequest
from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.shared.domain.value_objects.entity_id import EntityId


class UpdateStoryDraftUseCase:
    """Use case for updating a story draft."""
    
    def __init__(self, repository: StoryDraftRepository):
        """
        Initialize use case.
        
        Args:
            repository: Story draft repository
        """
        self._repository = repository
    
    async def execute(
        self,
        draft_id: str,
        request: UpdateStoryDraftRequest,
    ) -> Optional[StoryDraftEntity]:
        """
        Execute update story draft use case.
        
        Args:
            draft_id: Draft UUID string
            request: UpdateStoryDraftRequest with fields to update
            
        Returns:
            StoryDraftEntity if updated, None if not found
        """
        entity_id = EntityId.from_string(draft_id)
        draft = await self._repository.find_by_id(entity_id.value)
        
        if not draft:
            return None
        
        draft.update_draft(
            title=request.title,
            description=request.description,
            acceptance_criteria=request.acceptance_criteria,
        )
        
        updated = await self._repository.save(draft)
        
        return updated
