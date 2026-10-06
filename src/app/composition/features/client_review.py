"""
Client Review feature dependency composition.

All dependency wiring for the public, access-code based project review.

Dependencies:
- Repositories: Story (shared), Project (shared, looked up by access code)

Use Cases:
- Get Client Review: A project's approved stories for an anonymous client stakeholder

Data Access:
Read-only feature. Nothing here writes.
"""

from fastapi import Depends

from src.app.composition.features.projects import get_project_repository
from src.app.composition.repositories import get_story_repository
from src.app.features.client_review.application.use_cases.get_client_review import GetClientReviewUseCase
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository


async def get_get_client_review_use_case(
    story_repo: StoryRepository = Depends(get_story_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> GetClientReviewUseCase:
    """GetClientReviewUseCase factory."""
    return GetClientReviewUseCase(story_repo, project_repo)
