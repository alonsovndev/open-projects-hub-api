"""Mapper for refinement bulk operations."""

from src.app.features.refinement.application.dtos.refinement_dto import ApproveDraftsBulkResponse, BulkApprovedStory
from src.app.features.stories.application.dtos.story_dto import StoryResponse


def to_approve_drafts_bulk_response(stories: list[StoryResponse]) -> ApproveDraftsBulkResponse:
    """Build an ApproveDraftsBulkResponse from a list of created StoryResponse objects."""
    return ApproveDraftsBulkResponse(
        approved_count=len(stories),
        stories=[BulkApprovedStory(id=str(s.id), title=s.title) for s in stories],
    )
