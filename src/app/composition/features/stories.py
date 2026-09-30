"""
Stories feature dependency composition.

All dependency wiring for user story management use cases.

Dependencies:
- Infrastructure: Database session
- Repositories: StoryRepository (shared, also used by refinement)

Use Cases:
- Create Story: Manual story creation (non-AI workflow)
- List Stories: Retrieve all stories with filtering
- Get Story: Retrieve single story by ID
- Update Story: Modify story details
- Delete Story: Remove story
- Assign Story: Assign story to team member
- Get Stories by Project: Filter stories by project ID

Story Lifecycle:
Stories can be created through two paths:
1. Manual creation (this feature)
2. AI generation + approval (refinement feature)

Once created, stories are managed through this feature's CRUD operations.

Usage:
    from src.app.composition import get_create_story_use_case

    @router.post("")
    async def create_story(
        use_case: CreateStoryUseCase = Depends(get_create_story_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends

from src.app.composition.features.projects import get_project_repository
from src.app.composition.repositories import get_story_repository, get_user_repository
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.application.use_cases.assign_story import AssignStoryUseCase
from src.app.features.stories.application.use_cases.create_story import CreateStoryUseCase
from src.app.features.stories.application.use_cases.delete_story import DeleteStoryUseCase
from src.app.features.stories.application.use_cases.get_stories_by_project import GetStoriesByProjectUseCase
from src.app.features.stories.application.use_cases.get_story_by_id import GetStoryByIdUseCase
from src.app.features.stories.application.use_cases.list_stories import ListStoriesUseCase
from src.app.features.stories.application.use_cases.update_story import UpdateStoryUseCase
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository


# Use case factories
async def get_create_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> CreateStoryUseCase:
    """CreateStoryUseCase factory."""
    return CreateStoryUseCase(repository, project_repository)


async def get_list_stories_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> ListStoriesUseCase:
    """ListStoriesUseCase factory."""
    return ListStoriesUseCase(repository)


async def get_get_story_by_id_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> GetStoryByIdUseCase:
    """GetStoryByIdUseCase factory."""
    return GetStoryByIdUseCase(repository)


async def get_update_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> UpdateStoryUseCase:
    """UpdateStoryUseCase factory."""
    return UpdateStoryUseCase(repository)


async def get_delete_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> DeleteStoryUseCase:
    """DeleteStoryUseCase factory."""
    return DeleteStoryUseCase(repository)


async def get_assign_story_use_case(
    repository: StoryRepository = Depends(get_story_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> AssignStoryUseCase:
    """AssignStoryUseCase factory."""
    return AssignStoryUseCase(repository, user_repository)


async def get_get_stories_by_project_use_case(
    repository: StoryRepository = Depends(get_story_repository),
) -> GetStoriesByProjectUseCase:
    """GetStoriesByProjectUseCase factory."""
    return GetStoriesByProjectUseCase(repository)
