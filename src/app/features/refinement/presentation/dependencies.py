"""Dependency injection for refinement feature."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.refinement.application.use_cases.approve_draft import ApproveDraftUseCase
from src.app.features.refinement.application.use_cases.approve_drafts_bulk import ApproveDraftsBulkUseCase
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import GenerateStoriesFromNotesUseCase
from src.app.features.refinement.application.use_cases.update_story_draft import UpdateStoryDraftUseCase
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.infrastructure.ai.ai_factory import create_ai_service
from src.app.features.refinement.infrastructure.ai.ai_service import AIService
from src.app.features.refinement.infrastructure.repositories.story_draft_repository_impl import (
    StoryDraftRepositoryImpl,
)
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.shared.presentation.dependencies import get_database_session


async def get_ai_service() -> AIService:
    """Get AI service instance (singleton per app lifecycle)."""
    return create_ai_service()


async def get_draft_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryDraftRepository:
    """
    Get story draft repository instance.
    
    Args:
        session: Database session
        
    Returns:
        StoryDraftRepository interface
    """
    return StoryDraftRepositoryImpl(session)


async def get_story_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryRepository:
    """
    Get story repository instance.
    
    Args:
        session: Database session
        
    Returns:
        StoryRepository interface
    """
    return StoryRepositoryImpl(session)


async def get_update_draft_use_case(
    repository: StoryDraftRepository = Depends(get_draft_repository),
) -> UpdateStoryDraftUseCase:
    """
    Get UpdateStoryDraftUseCase instance.
    
    Args:
        repository: Story draft repository
        
    Returns:
        UpdateStoryDraftUseCase instance
    """
    return UpdateStoryDraftUseCase(repository)


async def get_generate_stories_use_case(
    repository: StoryDraftRepository = Depends(get_draft_repository),
    ai_service: AIService = Depends(get_ai_service),
) -> GenerateStoriesFromNotesUseCase:
    """
    Get GenerateStoriesFromNotesUseCase instance.
    
    Args:
        repository: Story draft repository
        ai_service: AI service
        
    Returns:
        GenerateStoriesFromNotesUseCase instance
    """
    return GenerateStoriesFromNotesUseCase(repository, ai_service)


async def get_approve_draft_use_case(
    draft_repository: StoryDraftRepository = Depends(get_draft_repository),
    story_repository: StoryRepository = Depends(get_story_repository),
) -> ApproveDraftUseCase:
    """
    Get ApproveDraftUseCase instance.
    
    Args:
        draft_repository: Story draft repository
        story_repository: Story repository
        
    Returns:
        ApproveDraftUseCase instance
    """
    return ApproveDraftUseCase(draft_repository, story_repository)


async def get_approve_drafts_bulk_use_case(
    draft_repository: StoryDraftRepository = Depends(get_draft_repository),
    story_repository: StoryRepository = Depends(get_story_repository),
) -> ApproveDraftsBulkUseCase:
    """
    Get ApproveDraftsBulkUseCase instance.
    
    Args:
        draft_repository: Story draft repository
        story_repository: Story repository
        
    Returns:
        ApproveDraftsBulkUseCase instance
    """
    return ApproveDraftsBulkUseCase(draft_repository, story_repository)
