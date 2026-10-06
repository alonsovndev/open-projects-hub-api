"""Client Review route: the public, read-only view a client stakeholder opens with an access code."""

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.params import Depends

from src.app.composition import get_get_client_review_use_case
from src.app.features.client_review.application.dtos.client_review_dto import ClientReviewResponse
from src.app.features.client_review.application.use_cases.get_client_review import GetClientReviewUseCase
from src.app.features.projects.domain.exceptions.project_exceptions import ProjectNotFoundError
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter


router = APIRouter()


@router.get("/{access_code}", response_model=ClientReviewResponse)
@limiter.limit("30/minute")
async def get_client_review(
    request: Request,
    access_code: str,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    use_case: GetClientReviewUseCase = Depends(get_get_client_review_use_case),
) -> ClientReviewResponse:
    """
    Get a project's approved stories by its access code.

    Public: no token. Limited to 30 requests a minute per IP because the access code is the
    only credential. Read-only and approved stories only; drafts never reach the stories table.

    Args:
        request: Required by the rate limiter
        access_code: The code the freelancer shared with their client, e.g. PRJ-7K3M9XQ2
        limit: Maximum number of stories per page
        offset: Number of stories to skip
        use_case: Injected GetClientReviewUseCase

    Returns:
        The project name, phase and approved stories in priority-then-age order

    Raises:
        404: No project has this access code (also returned for a malformed code)
        429: Rate limit exceeded
    """
    try:
        return await use_case.execute(access_code=access_code, limit=limit, offset=offset)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error
