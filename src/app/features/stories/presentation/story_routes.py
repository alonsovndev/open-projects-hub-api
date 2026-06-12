"""Story routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends

from src.app.composition import (
    get_assign_story_use_case,
    get_create_story_use_case,
    get_database_session,
    get_delete_story_use_case,
    get_get_stories_by_project_use_case,
    get_get_story_by_id_use_case,
    get_list_stories_use_case,
    get_update_story_use_case,
)
from src.app.composition.repositories import build_story_repository
from src.app.features.stories.application.dtos.story_dto import (
    AssignStoryRequest,
    CreateStoryRequest,
    StoryResponse,
    UpdateStoryRequest,
)
from src.app.features.stories.application.use_cases.assign_story import AssignStoryUseCase
from src.app.features.stories.application.use_cases.create_story import CreateStoryUseCase
from src.app.features.stories.application.use_cases.delete_story import DeleteStoryUseCase
from src.app.features.stories.application.use_cases.get_stories_by_project import GetStoriesByProjectUseCase
from src.app.features.stories.application.use_cases.get_story_by_id import GetStoryByIdUseCase
from src.app.features.stories.application.use_cases.list_stories import ListStoriesUseCase
from src.app.features.stories.application.use_cases.update_story import UpdateStoryUseCase
from src.app.features.stories.domain.exceptions.story_exceptions import StoryNotFoundError
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.domain.exceptions.domain_exceptions import ValidationError
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.presentation.auth_dependencies import get_current_user


router = APIRouter()


async def _authorize_story_owner_or_admin(story_id: str, current_user: dict[str, Any]) -> None:
    """Verify the current user is the story owner or an admin.

    Raises:
        HTTPException 400: Invalid story ID format
        HTTPException 403: Not authorized
        HTTPException 404: Story not found
    """
    user_role = current_user.get("role")
    if user_role == UserRole.ADMIN.value:
        return

    try:
        story_entity_id = EntityId.from_string(story_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid story ID format") from None

    async for session in get_database_session():
        story_repo = build_story_repository(session)
        story = await story_repo.find_by_id(story_entity_id.value)

        if not story:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")

        user_id = current_user.get("sub")
        if story.created_by.value != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this story. Only the creator or an admin can modify stories.",
            )
        return


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    payload: CreateStoryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: CreateStoryUseCase = Depends(get_create_story_use_case),
) -> StoryResponse:
    """
    Create a new story.

    Requires authentication. Anyone can create stories.
    The created_by user is extracted from the JWT token.

    Args:
        payload: CreateStoryRequest with story details (title, description, project_id, etc.)
        current_user: Current authenticated user (from JWT)
        use_case: Injected CreateStoryUseCase

    Returns:
        StoryResponse with created story data

    Raises:
        400: Validation failed (invalid title, priority, etc.)
        401: Unauthorized
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    try:
        return await use_case.execute(request=payload, created_by=user_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=PaginatedResponse[StoryResponse])
async def list_stories(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    project_id: str | None = Query(default=None),
    story_status: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: ListStoriesUseCase = Depends(get_list_stories_use_case),
) -> PaginatedResponse[StoryResponse]:
    """
    List stories with optional filters.

    Requires authentication.

    Args:
        limit: Maximum number of results (1-100, default 20)
        offset: Number of results to skip (default 0)
        project_id: Optional project filter
        story_status: Optional status filter (todo, in_progress, done)
        priority: Optional priority filter (low, medium, high)
        assigned_to: Optional assigned user filter
        current_user: Current authenticated user
        use_case: Injected ListStoriesUseCase

    Returns:
        PaginatedResponse containing pagination metadata and list of StoryResponse objects

    Raises:
        400: Invalid query parameters
        401: Unauthorized
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    return await use_case.execute(
        user_id=user_id,
        limit=limit,
        offset=offset,
        project_id=project_id,
        status=story_status,
        priority=priority,
        assigned_to=assigned_to,
    )


@router.get("/by-project/{project_id}", response_model=PaginatedResponse[StoryResponse])
async def get_stories_by_project(
    project_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: GetStoriesByProjectUseCase = Depends(get_get_stories_by_project_use_case),
) -> PaginatedResponse[StoryResponse]:
    """
    Get all stories for a specific project.

    Requires authentication.

    Args:
        project_id: Project UUID
        limit: Maximum number of results (1-100, default 20)
        offset: Number of results to skip (default 0)
        current_user: Current authenticated user
        use_case: Injected GetStoriesByProjectUseCase

    Returns:
        PaginatedResponse containing pagination metadata and list of StoryResponse objects

    Raises:
        401: Unauthorized
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    return await use_case.execute(
        project_id=str(project_id),
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story_by_id(
    story_id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: GetStoryByIdUseCase = Depends(get_get_story_by_id_use_case),
) -> StoryResponse:
    """
    Get story by ID.

    Requires authentication.

    Args:
        story_id: Story UUID
        current_user: Current authenticated user
        use_case: Injected GetStoryByIdUseCase

    Returns:
        StoryResponse with story data

    Raises:
        400: Invalid UUID
        401: Unauthorized
        404: Story not found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    try:
        return await use_case.execute(str(story_id), user_id=user_id)
    except StoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: UUID,
    payload: UpdateStoryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: UpdateStoryUseCase = Depends(get_update_story_use_case),
) -> StoryResponse:
    """
    Update story.

    Requires authentication. Only the story creator or an admin can update.
    Supports partial updates — only provided fields are changed.

    Args:
        story_id: Story UUID
        payload: UpdateStoryRequest with fields to update
        current_user: Current authenticated user
        use_case: Injected UpdateStoryUseCase

    Returns:
        StoryResponse with updated story data

    Raises:
        400: Validation failed
        401: Unauthorized
        403: Forbidden (not owner or admin)
        404: Story not found
        500: Internal server error
    """
    await _authorize_story_owner_or_admin(str(story_id), current_user)

    user_id = str(current_user["sub"])
    try:
        return await use_case.execute(story_id=str(story_id), request=payload, created_by=user_id)
    except StoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: DeleteStoryUseCase = Depends(get_delete_story_use_case),
) -> None:
    """
    Delete story.

    Requires authentication. Only the story creator or an admin can delete.

    Args:
        story_id: Story UUID
        current_user: Current authenticated user
        use_case: Injected DeleteStoryUseCase

    Raises:
        400: Invalid UUID
        401: Unauthorized
        403: Forbidden (not owner or admin)
        404: Story not found
        500: Internal server error
    """
    await _authorize_story_owner_or_admin(str(story_id), current_user)

    user_id = str(current_user["sub"])
    try:
        await use_case.execute(story_id=str(story_id), created_by=user_id)
    except StoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{story_id}/assign", response_model=StoryResponse)
async def assign_story(
    story_id: UUID,
    payload: AssignStoryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: AssignStoryUseCase = Depends(get_assign_story_use_case),
) -> StoryResponse:
    """
    Assign story to a user.

    Requires authentication.

    Args:
        story_id: Story UUID
        payload: AssignStoryRequest with user_id to assign
        current_user: Current authenticated user
        use_case: Injected AssignStoryUseCase

    Returns:
        StoryResponse with updated story data

    Raises:
        400: Validation failed
        401: Unauthorized
        404: Story not found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    try:
        return await use_case.execute(
            story_id=str(story_id),
            user_id=payload.user_id,
            created_by=user_id,
        )
    except StoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
