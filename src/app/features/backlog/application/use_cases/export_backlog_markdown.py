"""ExportBacklogMarkdownUseCase - renders a scoped backlog as a downloadable Markdown file."""

import re
from datetime import UTC, datetime
from uuid import UUID

from src.app.features.backlog.application.dtos.backlog_dto import MarkdownExport, MarkdownExportRequest
from src.app.features.backlog.domain.services.backlog_markdown_renderer import render_backlog_markdown
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.queries.backlog_query import BacklogQuery
from src.app.features.stories.domain.repositories.story_repository import StoryRepository
from src.app.shared.logging import get_logger


# A single export is one document a person reads, so it is bounded rather than paged. MVP
# projects are far below this; a project that exceeds it needs a scoped export instead.
MAX_EXPORTED_STORIES = 1000


class ExportBacklogMarkdownUseCase:
    """Generates the Markdown artifact that is the MVP's shareable deliverable."""

    def __init__(self, story_repository: StoryRepository, project_repository: ProjectRepository):
        self._story_repository = story_repository
        self._project_repository = project_repository

    async def execute(self, project_id: UUID, scope: MarkdownExportRequest) -> MarkdownExport:
        """
        Render the project's backlog within the requested scope.

        An empty result is not an error: the document is still produced, and story_count
        lets the caller warn that it contains nothing.

        Args:
            project_id: The project to export
            scope: Optional status and date-range narrowing

        Returns:
            The rendered export with its suggested filename and story count

        Raises:
            ProjectNotFoundError: If the project does not exist
        """
        log = get_logger(__name__)
        log.info(
            "Exporting backlog to Markdown",
            extra={"event_type": "backlog.export.started", "project_id": str(project_id)},
        )

        found = await self._project_repository.find_by_id(project_id)
        if found is None:
            raise ProjectNotFoundError(str(project_id))
        project, _client_name = found

        query = BacklogQuery(
            project_id=project_id,
            status=scope.status,
            created_from=scope.date_from,
            created_to=scope.date_to,
            limit=MAX_EXPORTED_STORIES,
        )

        # Counted before rendering so a document cut short by the cap can say so. Silently
        # returning a truncated backlog would be the one place this feature hides something
        # from the Admin instead of warning.
        matched = await self._story_repository.count_backlog(query)
        stories = await self._story_repository.find_backlog(query)

        generated_on = datetime.now(tz=UTC).date()
        content = render_backlog_markdown(project, stories, generated_on)
        filename = build_export_filename(project.name, generated_on.isoformat())

        truncated = matched > len(stories)
        if truncated:
            log.warning(
                "Backlog export truncated by the export cap",
                extra={
                    "event_type": "backlog.export.truncated",
                    "project_id": str(project_id),
                    "matched": matched,
                    "exported": len(stories),
                },
            )

        log.info(
            "Backlog exported",
            extra={
                "event_type": "backlog.export.success",
                "project_id": str(project_id),
                "story_count": len(stories),
            },
        )

        return MarkdownExport(
            filename=filename,
            content=content,
            story_count=len(stories),
            matched_count=matched,
        )


def build_export_filename(project_name: str, generated_on: str) -> str:
    """
    Build a safe download filename from the project name and date.

    The name reaches the client inside a Content-Disposition header, so it is reduced to
    ASCII word characters and hyphens — quotes, newlines or path separators in a project
    name must not be able to shape the header or the saved path.

    Args:
        project_name: The project's display name
        generated_on: ISO date stamp

    Returns:
        A filename such as "acme-portal-backlog-2026-09-20.md"
    """
    slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")
    return f"{slug or 'project'}-backlog-{generated_on}.md"
