"""Unit tests for ExportBacklogMarkdownUseCase."""

from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.backlog.application.dtos.backlog_dto import MarkdownExportRequest
from src.app.features.backlog.application.use_cases.export_backlog_markdown import (
    MAX_EXPORTED_STORIES,
    ExportBacklogMarkdownUseCase,
    build_export_filename,
)
from src.app.features.backlog.domain.services.backlog_markdown_renderer import EMPTY_BACKLOG_NOTICE
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import TEST_WORKSPACE_UUID, make_request_context


def build_project(name: str = "Acme Portal") -> ProjectEntity:
    """Build a project to export."""
    return ProjectEntity.create(
        workspace_id=EntityId.generate(),
        name=name,
        code="ACME",
        created_by=EntityId.generate(),
        client_id=EntityId.generate(),
    )


def build_story(title: str = "Story", acceptance_criteria: list[str] | None = None) -> StoryEntity:
    """Build a backlog story."""
    return StoryEntity.create(
        title=title,
        project_id=EntityId.generate(),
        created_by=EntityId.generate(),
        description="Description",
        acceptance_criteria=acceptance_criteria,
    )


def build_use_case(stories: list[StoryEntity], project: ProjectEntity | None = None):
    """Wire the use case over mock repositories."""
    story_repo, project_repo = AsyncMock(), AsyncMock()
    project_repo.find_by_id.return_value = (project or build_project(), "Acme Ltd")
    story_repo.find_backlog.return_value = stories
    story_repo.count_backlog.return_value = len(stories)
    return ExportBacklogMarkdownUseCase(story_repo, project_repo), story_repo


class TestExportContent:
    """Test what ends up in the exported document."""

    @pytest.mark.asyncio
    async def test_export_contains_the_stories_and_their_criteria(self):
        """Test that the rendered document carries the backlog."""
        use_case, _ = build_use_case([build_story(title="Login", acceptance_criteria=["User can log in"])])

        export = await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        assert "## 1. Login" in export.content
        assert "- User can log in" in export.content
        assert export.story_count == 1

    @pytest.mark.asyncio
    async def test_filename_carries_the_project_and_date(self):
        """Test that the suggested filename identifies the export's scope."""
        use_case, _ = build_use_case([build_story()])

        export = await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        assert export.filename.startswith("acme-portal-backlog-")
        assert export.filename.endswith(".md")


class TestExportScope:
    """Test that scope parameters reach the query."""

    @pytest.mark.asyncio
    async def test_export_is_scoped_to_the_requested_project(self):
        """Test that only the named project's stories are queried."""
        project_id = uuid4()
        use_case, story_repo = build_use_case([])

        await use_case.execute(project_id=project_id, scope=MarkdownExportRequest(), ctx=make_request_context())

        assert story_repo.find_backlog.call_args.args[0].project_id == project_id

    @pytest.mark.asyncio
    async def test_status_filter_reaches_the_query(self):
        """Test that a status scope narrows the query."""
        use_case, story_repo = build_use_case([])

        await use_case.execute(
            project_id=uuid4(), scope=MarkdownExportRequest(status=StoryStatus.DONE), ctx=make_request_context()
        )

        assert story_repo.find_backlog.call_args.args[0].status == StoryStatus.DONE

    @pytest.mark.asyncio
    async def test_date_range_reaches_the_query(self):
        """Test that a date scope narrows the query."""
        use_case, story_repo = build_use_case([])

        await use_case.execute(
            project_id=uuid4(),
            scope=MarkdownExportRequest(date_from=date(2026, 1, 1), date_to=date(2026, 6, 30)),
            ctx=make_request_context(),
        )

        query = story_repo.find_backlog.call_args.args[0]
        assert query.created_from == date(2026, 1, 1)
        assert query.created_to == date(2026, 6, 30)

    @pytest.mark.asyncio
    async def test_an_empty_scope_exports_everything(self):
        """Test that an absent filter leaves the query unnarrowed."""
        use_case, story_repo = build_use_case([])

        await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        query = story_repo.find_backlog.call_args.args[0]
        assert query.status is None
        assert query.created_from is None
        assert query.created_to is None

    def test_inverted_date_range_is_rejected(self):
        """An inverted range would silently export nothing, so it is refused up front."""
        with pytest.raises(ValueError, match="dateFrom cannot be later than dateTo"):
            MarkdownExportRequest(date_from=date(2026, 6, 30), date_to=date(2026, 1, 1))

    def test_unknown_scope_fields_are_rejected(self):
        """Test that a typo in a filter name fails loudly rather than being ignored."""
        with pytest.raises(ValueError):
            MarkdownExportRequest.model_validate({"statuss": "done"})


class TestEmptyAndMissing:
    """Test the empty-scope guard and the unknown project."""

    @pytest.mark.asyncio
    async def test_empty_scope_still_returns_a_document(self):
        """FR-004-06: warn rather than fail, so the Admin still gets a template."""
        use_case, _ = build_use_case([])

        export = await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        assert export.story_count == 0
        assert EMPTY_BACKLOG_NOTICE in export.content
        assert export.filename.endswith(".md")

    @pytest.mark.asyncio
    async def test_unknown_project_is_rejected(self):
        """Test that exporting a missing project raises."""
        story_repo, project_repo = AsyncMock(), AsyncMock()
        project_repo.find_by_id.return_value = None
        use_case = ExportBacklogMarkdownUseCase(story_repo, project_repo)

        with pytest.raises(ProjectNotFoundError):
            await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        story_repo.find_backlog.assert_not_called()


class TestExportTruncation:
    """The export is capped, and a capped document must say so."""

    @pytest.mark.asyncio
    async def test_an_uncapped_export_is_not_flagged_as_truncated(self):
        """Test that a normal export reports no truncation."""
        use_case, story_repo = build_use_case([build_story(), build_story()])
        story_repo.count_backlog.return_value = 2

        export = await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        assert export.matched_count == 2
        assert export.is_truncated is False

    @pytest.mark.asyncio
    async def test_a_capped_export_reports_what_was_left_out(self):
        """A scope larger than the cap must not look complete."""
        use_case, story_repo = build_use_case([build_story()])
        story_repo.count_backlog.return_value = 1200

        export = await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        assert export.story_count == 1
        assert export.matched_count == 1200
        assert export.is_truncated is True

    @pytest.mark.asyncio
    async def test_the_cap_is_applied_to_the_query(self):
        """Test that the export asks for at most MAX_EXPORTED_STORIES."""
        use_case, story_repo = build_use_case([])

        await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        assert story_repo.find_backlog.call_args.args[0].limit == MAX_EXPORTED_STORIES

    @pytest.mark.asyncio
    async def test_the_count_ignores_the_cap(self):
        """The count must describe the scope, not the page, or truncation is invisible."""
        use_case, story_repo = build_use_case([build_story()])
        story_repo.count_backlog.return_value = 1200

        await use_case.execute(project_id=uuid4(), scope=MarkdownExportRequest(), ctx=make_request_context())

        counted = story_repo.count_backlog.call_args.args[0]
        queried = story_repo.find_backlog.call_args.args[0]
        assert counted.project_id == queried.project_id
        assert counted.status == queried.status


class TestExportFilename:
    """Test filename construction, which reaches a response header."""

    def test_name_is_slugified(self):
        """Test that spaces and case become a hyphenated slug."""
        assert build_export_filename("Acme Portal", "2026-09-20") == "acme-portal-backlog-2026-09-20.md"

    def test_header_breaking_characters_are_stripped(self):
        """A quote or newline in a project name must not shape the header."""
        filename = build_export_filename('Acme" \r\nX-Injected: yes', "2026-09-20")

        assert '"' not in filename
        assert "\n" not in filename
        assert "\r" not in filename

    def test_path_separators_are_stripped(self):
        """A slash must not be able to steer where the file is saved."""
        filename = build_export_filename("../../etc/passwd", "2026-09-20")

        assert "/" not in filename
        assert ".." not in filename

    def test_a_name_with_no_usable_characters_falls_back(self):
        """Test that an unslugifiable name still yields a valid filename."""
        assert build_export_filename("***", "2026-09-20") == "project-backlog-2026-09-20.md"


class TestExportWorkspaceBoundary:
    @pytest.mark.asyncio
    async def test_the_project_and_its_stories_are_read_within_the_callers_workspace(self):
        use_case, story_repo = build_use_case([])
        project_id = uuid4()

        await use_case.execute(project_id=project_id, scope=MarkdownExportRequest(), ctx=make_request_context())

        use_case._project_repository.find_by_id.assert_awaited_once_with(project_id, workspace_id=TEST_WORKSPACE_UUID)
        assert story_repo.find_backlog.call_args.args[0].workspace_id == TEST_WORKSPACE_UUID
