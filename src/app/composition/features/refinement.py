"""
Refinement feature dependency composition.

All dependency wiring for AI-powered story refinement use cases.

Dependencies:
- Infrastructure: Database session, AI service (singleton)
- Repositories: StoryRepository (shared, also used by stories feature), ProjectRepository

Use Cases:
- Generate Stories: AI-powered story generation from raw notes; nothing is persisted
- Approve Story: Save one approved refined story to the backlog
- Approve Stories Bulk: Batch approval of several refined stories

External Services:
The provider for a run is chosen per request by RefinementProviderResolver (ai_config):
the platform's singleton client when free credits are being spent, or a client built
from the caller's own stored key when they selected one of their providers.

Domain Logic:
Refined stories live only in the client until approved. Approval sends the story
content and creates a Story entity; discarding one never touches the database.

Usage:
    from src.app.composition import get_generate_stories_use_case

    @router.post("/generate")
    async def generate_stories(
        use_case: GenerateStoriesUseCase = Depends(get_generate_stories_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends

from src.app.composition.features.ai_config import get_refinement_provider_resolver
from src.app.composition.features.projects import get_project_repository
from src.app.composition.repositories import get_story_repository, get_user_repository
from src.app.features.ai_config.application.services.refinement_provider_resolver import RefinementProviderResolver
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.refinement.application.use_cases.approve_stories_bulk import ApproveStoriesBulkUseCase
from src.app.features.refinement.application.use_cases.approve_story import ApproveStoryUseCase
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import (
    GenerateStoriesFromNotesUseCase,
)
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.features.user.domain.repositories.user_repository import UserRepository


# Use case factories
async def get_generate_stories_use_case(
    provider_resolver: RefinementProviderResolver = Depends(get_refinement_provider_resolver),
    user_repository: UserRepository = Depends(get_user_repository),
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> GenerateStoriesFromNotesUseCase:
    """
    GenerateStoriesFromNotesUseCase factory.

    Takes a provider resolver rather than a fixed AI service: which client serves a run
    depends on the provider the user selected and on whether they hold a key for it.
    """
    return GenerateStoriesFromNotesUseCase(provider_resolver, user_repository, project_repository)


async def get_approve_story_use_case(
    story_repository: StoryRepository = Depends(get_story_repository),
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> ApproveStoryUseCase:
    """ApproveStoryUseCase factory."""
    return ApproveStoryUseCase(story_repository, project_repository)


async def get_approve_stories_bulk_use_case(
    story_repository: StoryRepository = Depends(get_story_repository),
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> ApproveStoriesBulkUseCase:
    """ApproveStoriesBulkUseCase factory."""
    return ApproveStoriesBulkUseCase(story_repository, project_repository)
