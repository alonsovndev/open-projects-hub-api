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
The provider for a run is chosen per request by RefinementProviderResolver (ai_config):
the platform's singleton client when free credits are being spent, or a client built
from the caller's own stored key when they selected one of their providers.

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

from src.app.composition.features.ai_config import get_refinement_provider_resolver
from src.app.composition.infrastructure import get_database_session
from src.app.composition.repositories import get_story_repository, get_user_repository
from src.app.features.ai_config.application.services.refinement_provider_resolver import RefinementProviderResolver
from src.app.features.refinement.application.use_cases.approve_draft import ApproveDraftUseCase
from src.app.features.refinement.application.use_cases.approve_drafts_bulk import ApproveDraftsBulkUseCase
from src.app.features.refinement.application.use_cases.delete_story_draft import DeleteStoryDraftUseCase
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import (
    GenerateStoriesFromNotesUseCase,
)
from src.app.features.refinement.application.use_cases.list_story_drafts import ListStoryDraftsUseCase
from src.app.features.refinement.application.use_cases.update_story_draft import UpdateStoryDraftUseCase
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.infrastructure.repositories.story_draft_repository_impl import StoryDraftRepositoryImpl
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository


# Feature-specific repository
async def get_draft_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryDraftRepository:
    """Draft repository factory (feature-specific)."""

    return StoryDraftRepositoryImpl(session)


# Use case factories
async def get_generate_stories_use_case(
    repository: StoryDraftRepository = Depends(get_draft_repository),
    provider_resolver: RefinementProviderResolver = Depends(get_refinement_provider_resolver),
    user_repository: UserRepository = Depends(get_user_repository),
) -> GenerateStoriesFromNotesUseCase:
    """
    GenerateStoriesFromNotesUseCase factory.

    Takes a provider resolver rather than a fixed AI service: which client serves a run
    depends on the provider the user selected and on whether they hold a key for it.
    """
    return GenerateStoriesFromNotesUseCase(repository, provider_resolver, user_repository)


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
