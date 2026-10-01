"""Mapper for refinement bulk operations."""

from src.app.features.refinement.application.dtos.refinement_dto import ApproveStoriesBulkResponse, BulkApprovedStory
from src.app.features.stories.application.dtos.story_dto import StoryResponse


def to_approve_stories_bulk_response(stories: list[StoryResponse]) -> ApproveStoriesBulkResponse:
    """Build an ApproveStoriesBulkResponse from a list of created StoryResponse objects."""
    return ApproveStoriesBulkResponse(
        approved_count=len(stories),
        stories=[BulkApprovedStory(id=str(s.id), title=s.title) for s in stories],
    )
