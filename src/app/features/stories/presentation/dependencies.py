"""Dependency injection for story feature."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.stories.application.use_cases.assign_story import AssignStoryUseCase
from src.app.features.stories.application.use_cases.create_story import CreateStoryUseCase
from src.app.features.stories.application.use_cases.delete_story import DeleteStoryUseCase
from src.app.features.stories.application.use_cases.get_stories_by_project import GetStoriesByProjectUseCase
from src.app.features.stories.application.use_cases.get_story_by_id import GetStoryByIdUseCase
from src.app.features.stories.application.use_cases.list_stories import ListStoriesUseCase
from src.app.features.stories.application.use_cases.update_story import UpdateStoryUseCase
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.shared.presentation.dependencies import get_database_session


async def get_story_repository(
    session: AsyncSession = Depends(get_database_session),
) -> StoryRepository:
    """
    Get story repository instance.
    
    Args:
        session: Database session
        
    Returns:
        StoryRepository instance
    """
    return StoryRepositoryImpl(session)


async def get_create_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> CreateStoryUseCase:
    """Get CreateStoryUseCase instance."""
    return CreateStoryUseCase(repository)


async def get_list_stories_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> ListStoriesUseCase:
    """Get ListStoriesUseCase instance."""
    return ListStoriesUseCase(repository)


async def get_get_story_by_id_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> GetStoryByIdUseCase:
    """Get GetStoryByIdUseCase instance."""
    return GetStoryByIdUseCase(repository)


async def get_update_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> UpdateStoryUseCase:
    """Get UpdateStoryUseCase instance."""
    return UpdateStoryUseCase(repository)


async def get_delete_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> DeleteStoryUseCase:
    """Get DeleteStoryUseCase instance."""
    return DeleteStoryUseCase(repository)


async def get_assign_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> AssignStoryUseCase:
    """Get AssignStoryUseCase instance."""
    return AssignStoryUseCase(repository)


async def get_get_stories_by_project_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> GetStoriesByProjectUseCase:
    """Get GetStoriesByProjectUseCase instance."""
    return GetStoriesByProjectUseCase(repository)