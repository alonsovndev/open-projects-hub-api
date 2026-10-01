"""Tests for ApproveStoryUseCase: a refined story is persisted only when approved."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.refinement.application.dtos.refinement_dto import ApproveStoryRequest
from src.app.features.refinement.application.use_cases.approve_story import ApproveStoryUseCase
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import TEST_WORKSPACE_UUID, make_request_context


def build_request(**overrides) -> ApproveStoryRequest:
    fields = {
        "project_id": str(EntityId.generate().value),
        "title": "Refined title",
        "description": "Refined description",
        "acceptance_criteria": ["User can enter credentials", "User sees dashboard"],
    }
    return ApproveStoryRequest(**{**fields, **overrides})


def build_use_case(project_exists: bool = True):
    story_repository = AsyncMock()
    story_repository.save.side_effect = lambda story: story
    project_repository = AsyncMock()
    project_repository.exists.return_value = project_exists
    return ApproveStoryUseCase(story_repository, project_repository), story_repository, project_repository


class TestApproveStoryUseCase:
    @pytest.mark.asyncio
    async def test_saves_story_and_returns_response(self):
        use_case, story_repository, _ = build_use_case()

        result = await use_case.execute(build_request(), ctx=make_request_context())

        assert isinstance(result, StoryResponse)
        assert result.title == "Refined title"
        story_repository.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_carries_acceptance_criteria_as_a_list(self):
        use_case, story_repository, _ = build_use_case()

        await use_case.execute(build_request(), ctx=make_request_context())

        # Assert on the entity handed to the repository, not on the mock's return value —
        # the latter would pass no matter what the use case built.
        saved_story = story_repository.save.call_args.args[0]
        assert saved_story.acceptance_criteria == ["User can enter credentials", "User sees dashboard"]
        assert saved_story.description == "Refined description"

    @pytest.mark.asyncio
    async def test_creator_is_the_caller(self):
        use_case, story_repository, _ = build_use_case()
        ctx = make_request_context()

        await use_case.execute(build_request(), ctx=ctx)

        assert story_repository.save.call_args.args[0].created_by == ctx.user_id

    @pytest.mark.asyncio
    async def test_creates_story_without_description(self):
        use_case, _, _ = build_use_case()

        result = await use_case.execute(build_request(description=None), ctx=make_request_context())

        assert result.description is None

    @pytest.mark.asyncio
    async def test_project_outside_the_workspace_is_not_found_and_nothing_is_saved(self):
        use_case, story_repository, project_repository = build_use_case(project_exists=False)
        request = build_request()

        with pytest.raises(NotFoundError):
            await use_case.execute(request, ctx=make_request_context())

        project_repository.exists.assert_awaited_once()
        assert project_repository.exists.call_args.kwargs["workspace_id"] == TEST_WORKSPACE_UUID
        story_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_story_save_fails(self):
        use_case, story_repository, _ = build_use_case()
        story_repository.save.side_effect = None
        story_repository.save.return_value = None

        with pytest.raises(ValueError, match="Failed to create story"):
            await use_case.execute(build_request(), ctx=make_request_context())

    def test_request_rejects_blank_title(self):
        with pytest.raises(ValueError, match="title"):
            build_request(title="   ")

    def test_request_rejects_title_longer_than_the_stories_table_allows(self):
        with pytest.raises(ValueError, match="title"):
            build_request(title="a" * 256)

    @pytest.mark.parametrize("criteria", [[""], ["   "], ["a" * 501]])
    def test_request_rejects_invalid_acceptance_criteria(self, criteria):
        with pytest.raises(ValueError, match="criteri"):
            build_request(acceptance_criteria=criteria)
