"""
Refinement feature dependency composition.

All dependency wiring for AI-powered story refinement use cases.

Dependencies:
- Infrastructure: Database session, AI service (singleton)
- Repositories:
  - DraftRepository (feature-specific, defined here)
  - StoryRepository (shared, also used by stories feature)

Use Cases:
- Generate Stories: AI-powered story generation from high-level descriptions
- Update Draft: Modify AI-generated story draft
- Approve Draft: Convert approved draft into official story
- Approve Drafts Bulk: Batch approval of multiple drafts

External Services:
Uses Gemini AI service (singleton) for natural language processing and
story generation. AI service lifecycle managed by infrastructure layer.

Domain Logic:
Drafts are temporary entities that exist during refinement workflow.
Once approved, draft data is converted to Story entities and the draft
is marked as processed.

Usage:
    from src.app.composition import get_generate_stories_use_case

    @router.post("/generate")
    async def generate_stories(
        use_case: GenerateStoriesUseCase = Depends(get_generate_stories_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.composition.infrastructure import get_ai_service, get_database_session
from src.app.composition.repositories import get_story_repository
from src.app.features.refinement.application.use_cases.approve_draft import ApproveDraftUseCase
from src.app.features.refinement.application.use_cases.approve_drafts_bulk import ApproveDraftsBulkUseCase
from src.app.features.refinement.application.use_cases.delete_story_draft import DeleteStoryDraftUseCase
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import (
    GenerateStoriesFromNotesUseCase,
)
from src.app.features.refinement.application.use_cases.list_story_drafts import ListStoryDraftsUseCase
from src.app.features.refinement.application.use_cases.update_story_draft import UpdateStoryDraftUseCase
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.features.refinement.infrastructure.repositories.story_draft_repository_impl import StoryDraftRepositoryImpl
from src.app.features.stories.domain.repositories.story_repository import StoryRepository


# Feature-specific repository
async def get_draft_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryDraftRepository:
    """Draft repository factory (feature-specific)."""

    return StoryDraftRepositoryImpl(session)


# Use case factories
async def get_generate_stories_use_case(
    repository: StoryDraftRepository = Depends(get_draft_repository),
    ai_service: AIService = Depends(get_ai_service),
) -> GenerateStoriesFromNotesUseCase:
    """
    GenerateStoriesFromNotesUseCase factory.

    Depends on AI service singleton for story generation.
    """
    return GenerateStoriesFromNotesUseCase(repository, ai_service)


async def get_update_draft_use_case(
    repository: StoryDraftRepository = Depends(get_draft_repository),
) -> UpdateStoryDraftUseCase:
    """UpdateStoryDraftUseCase factory."""
    return UpdateStoryDraftUseCase(repository)


async def get_list_drafts_use_case(
    repository: StoryDraftRepository = Depends(get_draft_repository),
) -> ListStoryDraftsUseCase:
    """ListStoryDraftsUseCase factory."""
    return ListStoryDraftsUseCase(repository)


async def get_delete_draft_use_case(
    repository: StoryDraftRepository = Depends(get_draft_repository),
) -> DeleteStoryDraftUseCase:
    """DeleteStoryDraftUseCase factory."""
    return DeleteStoryDraftUseCase(repository)


async def get_approve_draft_use_case(
    draft_repository: StoryDraftRepository = Depends(get_draft_repository),
    story_repository: StoryRepository = Depends(get_story_repository),
) -> ApproveDraftUseCase:
    """
    ApproveDraftUseCase factory.

    Depends on both draft and story repositories to convert drafts to stories.
    """
    return ApproveDraftUseCase(draft_repository, story_repository)


async def get_approve_drafts_bulk_use_case(
    draft_repository: StoryDraftRepository = Depends(get_draft_repository),
    story_repository: StoryRepository = Depends(get_story_repository),
) -> ApproveDraftsBulkUseCase:
    """
    ApproveDraftsBulkUseCase factory.

    Bulk operation for approving multiple drafts at once.
    """
    return ApproveDraftsBulkUseCase(draft_repository, story_repository)
