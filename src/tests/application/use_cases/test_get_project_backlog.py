"""Unit tests for GetProjectBacklogUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.app.features.backlog.application.use_cases.get_project_backlog import GetProjectBacklogUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


def build_project() -> ProjectEntity:
    """Build a project the backlog belongs to."""
    return ProjectEntity.create(
        workspace_id=EntityId.generate(),
        name="Acme Portal",
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


class TestGetProjectBacklogUseCase:
    """Test the structured backlog read."""

    @pytest.mark.asyncio
    async def test_returns_stories_with_acceptance_criteria(self):
        """Test that criteria reach the response as a list."""
        project_id = uuid4()
        story_repo, project_repo = AsyncMock(), AsyncMock()
        project_repo.find_by_id.return_value = (build_project(), "Acme Ltd")
        story_repo.count_backlog.return_value = 1
        story_repo.find_backlog.return_value = [build_story(acceptance_criteria=["User can log in"])]

        use_case = GetProjectBacklogUseCase(story_repo, project_repo)

        result = await use_case.execute(project_id=project_id, ctx=make_request_context())

        assert result.total == 1
        assert result.items[0].acceptance_criteria == ["User can log in"]

    @pytest.mark.asyncio
    async def test_scopes_the_query_to_the_requested_project(self):
        """Test that the repository is asked only for that project's stories."""
        project_id = uuid4()
        story_repo, project_repo = AsyncMock(), AsyncMock()
        project_repo.find_by_id.return_value = (build_project(), "Acme Ltd")
        story_repo.count_backlog.return_value = 0
        story_repo.find_backlog.return_value = []

        use_case = GetProjectBacklogUseCase(story_repo, project_repo)

        await use_case.execute(project_id=project_id, ctx=make_request_context(), limit=25, offset=50)

        query = story_repo.find_backlog.call_args.args[0]
        assert query.project_id == project_id
        assert query.limit == 25
        assert query.offset == 50

    @pytest.mark.asyncio
    async def test_reports_the_page_derived_from_the_offset(self):
        """Test that the pagination envelope is consistent with the offset."""
        story_repo, project_repo = AsyncMock(), AsyncMock()
        project_repo.find_by_id.return_value = (build_project(), "Acme Ltd")
        story_repo.count_backlog.return_value = 120
        story_repo.find_backlog.return_value = []

        use_case = GetProjectBacklogUseCase(story_repo, project_repo)

        result = await use_case.execute(project_id=uuid4(), ctx=make_request_context(), limit=50, offset=100)

        assert result.page == 3
        assert result.per_page == 50
        assert result.total == 120

    @pytest.mark.asyncio
    async def test_unknown_project_is_rejected(self):
        """Test that a missing project raises rather than returning an empty backlog."""
        story_repo, project_repo = AsyncMock(), AsyncMock()
        project_repo.find_by_id.return_value = None

        use_case = GetProjectBacklogUseCase(story_repo, project_repo)

        with pytest.raises(ProjectNotFoundError):
            await use_case.execute(project_id=uuid4(), ctx=make_request_context())

        story_repo.find_backlog.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_backlog_returns_an_empty_page(self):
        """Test that a project with no stories is not an error."""
        story_repo, project_repo = AsyncMock(), AsyncMock()
        project_repo.find_by_id.return_value = (build_project(), "Acme Ltd")
        story_repo.count_backlog.return_value = 0
        story_repo.find_backlog.return_value = []

        use_case = GetProjectBacklogUseCase(story_repo, project_repo)

        result = await use_case.execute(project_id=uuid4(), ctx=make_request_context())

        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_response_omits_internal_assignment_fields(self):
        """The backlog is stakeholder-facing, so it must not leak assignee or author."""
        story_repo, project_repo = AsyncMock(), AsyncMock()
        project_repo.find_by_id.return_value = (build_project(), "Acme Ltd")
        story_repo.count_backlog.return_value = 1
        story_repo.find_backlog.return_value = [build_story()]

        use_case = GetProjectBacklogUseCase(story_repo, project_repo)

        result = await use_case.execute(project_id=uuid4(), ctx=make_request_context())

        serialized = result.items[0].model_dump(by_alias=True)
        assert "assignedTo" not in serialized
        assert "createdBy" not in serialized

        now = datetime.now(tz=UTC)
        assert serialized["createdAt"] <= now.isoformat()
