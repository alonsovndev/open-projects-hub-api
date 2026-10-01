"""Tests for ApproveStoriesBulkUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.app.features.refinement.application.dtos.refinement_dto import ApproveStoriesBulkRequest, ApproveStoryRequest
from src.app.features.refinement.application.use_cases.approve_stories_bulk import ApproveStoriesBulkUseCase
from src.app.shared.domain.exceptions.domain_exceptions import NotFoundError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.tests.support.request_context import make_request_context


def build_story(project_id: str, title: str) -> ApproveStoryRequest:
    return ApproveStoryRequest(project_id=project_id, title=title, description="Description", acceptance_criteria=["A"])


def build_use_case(known_project_ids: set[str]):
    story_repository = AsyncMock()
    story_repository.save.side_effect = lambda story: story
    project_repository = AsyncMock()
    project_repository.exists.side_effect = lambda project_uuid, **_: str(project_uuid) in known_project_ids
    return ApproveStoriesBulkUseCase(story_repository, project_repository), story_repository


class TestApproveStoriesBulkUseCase:
    @pytest.mark.asyncio
    async def test_saves_every_story(self):
        project_id = str(EntityId.generate().value)
        use_case, story_repository = build_use_case({project_id})
        request = ApproveStoriesBulkRequest(stories=[build_story(project_id, "One"), build_story(project_id, "Two")])

        result = await use_case.execute(request, ctx=make_request_context())

        assert [story.title for story in result] == ["One", "Two"]
        assert story_repository.save.await_count == 2

    @pytest.mark.asyncio
    async def test_creator_is_the_caller_and_criteria_stay_a_list(self):
        project_id = str(EntityId.generate().value)
        use_case, story_repository = build_use_case({project_id})
        ctx = make_request_context()

        await use_case.execute(ApproveStoriesBulkRequest(stories=[build_story(project_id, "One")]), ctx=ctx)

        saved_story = story_repository.save.call_args.args[0]
        assert saved_story.created_by == ctx.user_id
        assert saved_story.acceptance_criteria == ["A"]

    @pytest.mark.asyncio
    async def test_a_foreign_project_rejects_the_whole_batch_before_any_save(self):
        own_project = str(EntityId.generate().value)
        foreign_project = str(EntityId.generate().value)
        use_case, story_repository = build_use_case({own_project})
        request = ApproveStoriesBulkRequest(
            stories=[build_story(own_project, "Mine"), build_story(foreign_project, "Theirs")]
        )

        with pytest.raises(NotFoundError):
            await use_case.execute(request, ctx=make_request_context())

        story_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_failed_save_removes_the_stories_already_created(self):
        project_id = str(EntityId.generate().value)
        use_case, story_repository = build_use_case({project_id})
        saved = []

        async def save_first_then_fail(story):
            if saved:
                raise RuntimeError("database down")
            saved.append(story)
            return story

        story_repository.save.side_effect = save_first_then_fail
        request = ApproveStoriesBulkRequest(stories=[build_story(project_id, "One"), build_story(project_id, "Two")])

        with pytest.raises(RuntimeError):
            await use_case.execute(request, ctx=make_request_context())

        story_repository.delete.assert_awaited_once()
        assert story_repository.delete.call_args.args[0] == saved[0].id.value

    def test_request_requires_at_least_one_story(self):
        with pytest.raises(ValueError, match="At least one story"):
            ApproveStoriesBulkRequest(stories=[])
