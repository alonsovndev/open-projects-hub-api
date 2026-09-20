"""
Backlog feature dependency composition.

All dependency wiring for the approved backlog view and its Markdown export.

Dependencies:
- Repositories: Story (shared), Project (for the project header and 404 check)

Use Cases:
- Get Project Backlog: Approved stories with acceptance criteria, in reading order
- Export Backlog Markdown: The same stories rendered as a downloadable document

Data Access:
Read-only feature. Nothing here writes, so no export artifact is persisted.

Usage:
    from src.app.composition import get_get_project_backlog_use_case

    @router.get("/{project_id}/backlog")
    async def get_backlog(
        use_case: GetProjectBacklogUseCase = Depends(get_get_project_backlog_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends

from src.app.composition.features.projects import get_project_repository
from src.app.composition.repositories import get_story_repository
from src.app.features.backlog.application.use_cases.export_backlog_markdown import ExportBacklogMarkdownUseCase
from src.app.features.backlog.application.use_cases.get_project_backlog import GetProjectBacklogUseCase
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository


async def get_get_project_backlog_use_case(
    story_repo: StoryRepository = Depends(get_story_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> GetProjectBacklogUseCase:
    """GetProjectBacklogUseCase factory."""
    return GetProjectBacklogUseCase(story_repo, project_repo)


async def get_export_backlog_markdown_use_case(
    story_repo: StoryRepository = Depends(get_story_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> ExportBacklogMarkdownUseCase:
    """ExportBacklogMarkdownUseCase factory."""
    return ExportBacklogMarkdownUseCase(story_repo, project_repo)
