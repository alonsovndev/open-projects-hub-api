"""Refinement API routes."""

from fastapi import APIRouter, Depends

from src.app.composition import (
    get_approve_stories_bulk_use_case,
    get_approve_story_use_case,
    get_generate_stories_use_case,
)
from src.app.features.refinement.application.dtos.refinement_dto import (
    ApproveStoriesBulkRequest,
    ApproveStoriesBulkResponse,
    ApproveStoryRequest,
    GenerateStoriesRequest,
    GenerateStoriesResponse,
)
from src.app.features.refinement.application.mappers.bulk_approve_mapper import to_approve_stories_bulk_response
from src.app.features.refinement.application.use_cases.approve_stories_bulk import ApproveStoriesBulkUseCase
from src.app.features.refinement.application.use_cases.approve_story import ApproveStoryUseCase
from src.app.features.refinement.application.use_cases.generate_stories_from_notes import (
    GenerateStoriesFromNotesUseCase,
)
from src.app.features.stories.application.dtos.story_dto import StoryResponse
from src.app.shared.application.request_context import RequestContext
from src.app.shared.presentation.auth_dependencies import require_editor


router = APIRouter(prefix="/refinement")


@router.post("/generate-stories", response_model=GenerateStoriesResponse)
async def generate_stories(
    payload: GenerateStoriesRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: GenerateStoriesFromNotesUseCase = Depends(get_generate_stories_use_case),
) -> GenerateStoriesResponse:
    """
    Generate refined stories from raw discovery notes (nothing is stored) using AI.

    Requires ADMIN role. Takes raw notes and generates 3-7 well-structured user stories.

    Args:
        payload: GenerateStoriesRequest with project_id and raw_notes
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected GenerateStoriesFromNotesUseCase

    Returns:
        GenerateStoriesResponse with generated stories

    Raises:
        422: Invalid or over-length input
        502: AI provider failure; the response echoes the raw notes back for retry
        500: Internal server error
    """
    return await use_case.execute(
        request=payload,
        ctx=ctx,
    )


@router.post("/approve-story", response_model=StoryResponse)
async def approve_story(
    payload: ApproveStoryRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: ApproveStoryUseCase = Depends(get_approve_story_use_case),
) -> StoryResponse:
    """
    Approve a refined story and save it to the backlog.

    Requires ADMIN role. Refined stories are not stored until this call, so the request
    carries the (possibly edited) story content.

    Args:
        payload: ApproveStoryRequest with project_id and the story content
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected ApproveStoryUseCase

    Returns:
        StoryResponse with created story data

    Raises:
        404: Project not found in the caller's workspace
        422: Invalid story content
    """
    return await use_case.execute(request=payload, ctx=ctx)


@router.post("/approve-stories", response_model=ApproveStoriesBulkResponse)
async def approve_stories_bulk(
    payload: ApproveStoriesBulkRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: ApproveStoriesBulkUseCase = Depends(get_approve_stories_bulk_use_case),
) -> ApproveStoriesBulkResponse:
    """
    Approve several refined stories and save them to the backlog.

    Requires ADMIN role. All-or-nothing: a foreign project or an invalid story rejects the
    whole batch before anything is saved, and a failure mid-save removes the stories
    already created.

    Args:
        payload: ApproveStoriesBulkRequest with the story contents
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected ApproveStoriesBulkUseCase

    Returns:
        ApproveStoriesBulkResponse with approved count and the created stories

    Raises:
        404: A project is not in the caller's workspace
        422: Empty batch or invalid story content
    """
    stories = await use_case.execute(request=payload, ctx=ctx)
    return to_approve_stories_bulk_response(stories)
