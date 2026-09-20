"""Refinement API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.app.composition import (
    get_approve_draft_use_case,
    get_approve_drafts_bulk_use_case,
    get_delete_draft_use_case,
    get_generate_stories_use_case,
    get_list_drafts_use_case,
    get_update_draft_use_case,
)
from src.app.features.refinement.application.dtos.refinement_dto import (
    ApproveDraftsBulkRequest,
    ApproveDraftsBulkResponse,
    GenerateStoriesRequest,
    GenerateStoriesResponse,
    ListStoryDraftsResponse,
    UpdateStoryDraftRequest,
)
from src.app.features.refinement.application.mappers.bulk_approve_mapper import to_approve_drafts_bulk_response
from src.app.features.refinement.application.use_cases.approve_draft import ApproveDraftUseCase
from src.app.features.refinement.application.use_cases.approve_drafts_bulk import ApproveDraftsBulkUseCase
from src.app.features.refinement.application.use_cases.delete_story_draft import DeleteStoryDraftUseCase
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import (
    GenerateStoriesFromNotesUseCase,
)
from src.app.features.refinement.application.use_cases.list_story_drafts import ListStoryDraftsUseCase
from src.app.features.refinement.application.use_cases.update_story_draft import UpdateStoryDraftUseCase
from src.app.features.refinement.domain.exceptions.refinement_exceptions import StoryDraftNotFoundError
from src.app.features.refinement.domain.value_objects.draft_status import DraftStatus
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.shared.presentation.auth_dependencies import require_admin


router = APIRouter(prefix="/refinement")


@router.get("/projects/{project_id}/drafts", response_model=ListStoryDraftsResponse)
async def list_drafts(
    project_id: UUID,
    status_filter: DraftStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: ListStoryDraftsUseCase = Depends(get_list_drafts_use_case),
) -> ListStoryDraftsResponse:
    """
    List story drafts for a project.

    Requires ADMIN role: drafts are unapproved AI output and are never exposed on a
    Viewer-facing read path.

    Args:
        project_id: Project UUID
        status_filter: Restrict to a single draft status, or omit for all
        limit: Maximum results
        offset: Number to skip
        current_user: Current authenticated admin user
        use_case: Injected ListStoryDraftsUseCase

    Returns:
        ListStoryDraftsResponse with the page of drafts and the matching total
    """
    return await use_case.execute(
        project_id=str(project_id),
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: DeleteStoryDraftUseCase = Depends(get_delete_draft_use_case),
) -> None:
    """
    Discard a story draft.

    Requires ADMIN role. A discarded draft is removed outright, so it can never reach the
    backlog or an export.

    Args:
        draft_id: Draft UUID
        current_user: Current authenticated admin user
        use_case: Injected DeleteStoryDraftUseCase

    Raises:
        404: Story draft not found
    """
    try:
        await use_case.execute(str(draft_id), deleted_by=str(current_user["sub"]))
    except StoryDraftNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.patch("/drafts/{draft_id}")
async def update_draft(
    draft_id: UUID,
    payload: UpdateStoryDraftRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: UpdateStoryDraftUseCase = Depends(get_update_draft_use_case),
) -> dict[str, str]:
    """
    Update a story draft.

    Requires ADMIN role. Allows editing the description of an existing draft.

    Args:
        draft_id: Draft UUID
        payload: UpdateStoryDraftRequest with fields to update
        current_user: Current authenticated admin user
        use_case: Injected UpdateStoryDraftUseCase

    Returns:
        Dict with draft ID on success

    Raises:
        404: Story draft not found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    try:
        result = await use_case.execute(
            draft_id=str(draft_id),
            request=payload,
            created_by=user_id,
        )
        return {"id": str(result.id.value)}

    except StoryDraftNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/generate-stories", response_model=GenerateStoriesResponse)
async def generate_stories(
    payload: GenerateStoriesRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: GenerateStoriesFromNotesUseCase = Depends(get_generate_stories_use_case),
) -> GenerateStoriesResponse:
    """
    Generate story drafts from raw discovery notes using AI.

    Requires ADMIN role. Takes raw notes and generates 3-7 well-structured user stories.

    Args:
        payload: GenerateStoriesRequest with project_id and raw_notes
        current_user: Current authenticated admin user
        use_case: Injected GenerateStoriesFromNotesUseCase

    Returns:
        GenerateStoriesResponse with generated stories

    Raises:
        400: Invalid or over-length input
        502: AI provider failure; the response echoes the raw notes back for retry
        500: Internal server error
    """
    return await use_case.execute(
        request=payload,
        created_by=str(current_user["sub"]),
    )


@router.post("/drafts/{draft_id}/approve", response_model=StoryResponse)
async def approve_draft(
    draft_id: UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: ApproveDraftUseCase = Depends(get_approve_draft_use_case),
) -> StoryResponse:
    """
    Approve a draft and convert it to a story.

    Requires ADMIN role. Converts the draft into a full story in the backlog
    and marks the draft as applied.

    Args:
        draft_id: Draft UUID
        current_user: Current authenticated admin user
        use_case: Injected ApproveDraftUseCase

    Returns:
        StoryResponse with created story data

    Raises:
        404: Story draft not found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    try:
        return await use_case.execute(str(draft_id), created_by=user_id)
    except StoryDraftNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/approve-drafts", response_model=ApproveDraftsBulkResponse)
async def approve_drafts_bulk(
    payload: ApproveDraftsBulkRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: ApproveDraftsBulkUseCase = Depends(get_approve_drafts_bulk_use_case),
) -> ApproveDraftsBulkResponse:
    """
    Approve multiple drafts and convert them to stories.

    Requires ADMIN role. Bulk operation to approve multiple drafts at once.

    Args:
        payload: ApproveDraftsBulkRequest with list of draft IDs
        current_user: Current authenticated admin user
        use_case: Injected ApproveDraftsBulkUseCase

    Returns:
        ApproveDraftsBulkResponse with approved count and list of created stories

    Raises:
        400: Invalid input or no drafts found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    stories = await use_case.execute(payload.draft_ids, created_by=user_id)

    if not stories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No drafts were found to approve",
        )

    return to_approve_drafts_bulk_response(stories)
