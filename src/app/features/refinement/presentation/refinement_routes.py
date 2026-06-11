"""Refinement API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.composition import (
    get_approve_draft_use_case,
    get_approve_drafts_bulk_use_case,
    get_generate_stories_use_case,
    get_update_draft_use_case,
)
from src.app.features.refinement.application.dtos.refinement_dto import (
    ApproveDraftsBulkRequest,
    ApproveDraftsBulkResponse,
    GenerateStoriesRequest,
    GenerateStoriesResponse,
    UpdateStoryDraftRequest,
)
from src.app.features.refinement.application.use_cases.approve_draft import ApproveDraftUseCase
from src.app.features.refinement.application.use_cases.approve_drafts_bulk import ApproveDraftsBulkUseCase
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import (
    GenerateStoriesFromNotesUseCase,
)
from src.app.features.refinement.application.use_cases.update_story_draft import UpdateStoryDraftUseCase
from src.app.features.refinement.infrastructure.ai.ai_service import AIServiceError
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.shared.presentation.auth_dependencies import require_admin


router = APIRouter(prefix="/refinement")


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
    result = await use_case.execute(
        draft_id=str(draft_id),
        request=payload,
        created_by=user_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story draft not found",
        )

    return {"id": str(result.id.value)}


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
        400: Invalid input
        502: AI service error
        500: Internal server error
    """
    try:
        return await use_case.execute(
            request=payload,
            created_by=str(current_user["sub"]),
        )
    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {e!s}",
        ) from e


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
    result = await use_case.execute(str(draft_id), created_by=user_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story draft not found",
        )

    return result


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

    return ApproveDraftsBulkResponse(
        approved_count=len(stories),
        stories=[{"id": s.id, "title": s.title} for s in stories],
    )
