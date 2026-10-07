"""Unit tests for GetClientReviewUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.client_review.application.use_cases.get_client_review import GetClientReviewUseCase
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.features.projects.domain.value_objects.access_code import generate_access_code
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


def build_project() -> ProjectEntity:
    return ProjectEntity.create(
        workspace_id=EntityId.generate(),
        name="Acme Portal",
        code="ACME",
        created_by=EntityId.generate(),
        client_id=EntityId.generate(),
    )


def build_story(project: ProjectEntity) -> StoryEntity:
    return StoryEntity.create(
        title="Log in",
        project_id=project.id,
        created_by=EntityId.generate(),
        description="As a client I want to log in",
        acceptance_criteria=["User can log in"],
    )


def build_use_case(project: ProjectEntity | None, stories: list[StoryEntity] | None = None):
    story_repository, project_repository = AsyncMock(), AsyncMock()
    project_repository.find_by_access_code.return_value = project
    story_repository.find_backlog.return_value = stories or []
    story_repository.count_backlog.return_value = len(stories or [])
    return GetClientReviewUseCase(story_repository, project_repository), story_repository, project_repository


class TestGetClientReviewUseCase:
    @pytest.mark.asyncio
    async def test_returns_the_projects_approved_stories(self):
        project = build_project()
        use_case, _, _ = build_use_case(project, [build_story(project)])

        result = await use_case.execute(access_code=project.access_code)

        assert result.project_name == "Acme Portal"
        assert result.phase == "discovery"
        assert result.total == 1
        assert result.stories[0].title == "Log in"
        assert result.stories[0].acceptance_criteria == ["User can log in"]

    @pytest.mark.asyncio
    async def test_reads_the_stories_of_the_workspace_the_code_belongs_to(self):
        """The workspace comes from the project the code resolves to, never from the caller."""
        project = build_project()
        use_case, story_repository, _ = build_use_case(project)

        await use_case.execute(access_code=project.access_code, limit=25, offset=50)

        query = story_repository.find_backlog.call_args.args[0]
        assert query.project_id == project.id.value
        assert query.workspace_id == project.workspace_id.value
        assert (query.limit, query.offset) == (25, 50)

    @pytest.mark.asyncio
    async def test_accepts_a_code_typed_in_lowercase_with_spaces(self):
        project = build_project()
        use_case, _, project_repository = build_use_case(project)

        await use_case.execute(access_code=f"  {project.access_code.lower()} ")

        project_repository.find_by_access_code.assert_awaited_once_with(project.access_code)

    @pytest.mark.asyncio
    async def test_an_unknown_code_is_not_found(self):
        use_case, story_repository, _ = build_use_case(None)

        with pytest.raises(ProjectNotFoundError):
            await use_case.execute(access_code=generate_access_code())

        story_repository.find_backlog.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("malformed_code", ["", "WEB", "PRJ-123456", "not a code"])
    async def test_a_malformed_code_is_not_found_without_a_database_lookup(self, malformed_code):
        use_case, _, project_repository = build_use_case(build_project())

        with pytest.raises(ProjectNotFoundError):
            await use_case.execute(access_code=malformed_code)

        project_repository.find_by_access_code.assert_not_awaited()
