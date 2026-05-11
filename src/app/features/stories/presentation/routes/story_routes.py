"""Story routes."""
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends

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
from src.app.features.stories.presentation.dependencies import (
    get_assign_story_use_case,
    get_create_story_use_case,
    get_delete_story_use_case,
    get_get_stories_by_project_use_case,
    get_get_story_by_id_use_case,
    get_list_stories_use_case,
    get_update_story_use_case,
)
from src.app.features.user.presentation.auth_dependencies import get_current_user
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.presentation.base_handler import BaseRouteHandler

router = APIRouter()
handler = BaseRouteHandler()


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    payload: CreateStoryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: CreateStoryUseCase = Depends(get_create_story_use_case),
) -> StoryResponse:
    """
    Create a new story.
    
    Requires authentication. Anyone can create stories.
    
    Args:
        payload: CreateStoryRequest with story details
        current_user: Current authenticated user
        use_case: Injected CreateStoryUseCase
        
    Returns:
        StoryResponse with created story data
        
    Raises:
        400: Validation failed
        401: Unauthorized
        500: Internal server error
    """
    return await handler.execute_with_payload_extraction(
        execute_fn=lambda user_id: use_case.execute(
            title=payload.title,
            project_id=payload.project_id,
            created_by=user_id,
            description=payload.description,
            priority=payload.priority,
            points=payload.points,
        ),
        current_user=current_user,
    )


@router.get("", response_model=list[StoryResponse])
async def list_stories(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    project_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    assigned_to: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: ListStoriesUseCase = Depends(get_list_stories_use_case),
) -> list[StoryResponse]:
    """
    List stories with filters.
    
    Requires authentication. Supports filtering by project, status, priority, and assignee.
    
    Args:
        limit: Maximum number of results (1-100, default 20)
        offset: Number of results to skip (default 0)
        project_id: Optional project filter
        status: Optional status filter (todo, in_progress, done)
        priority: Optional priority filter (low, medium, high)
        assigned_to: Optional assigned user filter
        current_user: Current authenticated user
        use_case: Injected ListStoriesUseCase
        
    Returns:
        List of StoryResponse objects
        
    Raises:
        400: Invalid query parameters
        401: Unauthorized
        500: Internal server error
    """
    async def execute():
        return await use_case.execute(
            limit=limit,
            offset=offset,
            project_id=project_id,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
        )
    
    return await handler.execute(execute)


@router.get("/by-project/{project_id}", response_model=list[StoryResponse])
async def get_stories_by_project(
    project_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: GetStoriesByProjectUseCase = Depends(get_get_stories_by_project_use_case),
) -> list[StoryResponse]:
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
        List of StoryResponse objects
        
    Raises:
        401: Unauthorized
        500: Internal server error
    """
    async def execute():
        return await use_case.execute(
            project_id=str(project_id),
            limit=limit,
            offset=offset,
        )
    
    return await handler.execute(execute)


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story_by_id(
    story_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
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
    async def execute():
        result = await use_case.execute(str(story_id))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        return result
    
    return await handler.execute(execute)


@router.patch("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: UUID,
    payload: UpdateStoryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: UpdateStoryUseCase = Depends(get_update_story_use_case),
) -> StoryResponse:
    """
    Update story.
    
    Requires authentication and authorization (story owner or admin).
    Supports partial updates.
    
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
    async def execute():
        # Authorization check: admin or story owner
        user_role = current_user.get("role")
        if user_role != UserRole.ADMIN.value:
            # Not admin - check if user is story owner
            from src.app.shared.presentation.dependencies import get_database_session
            from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
            
            try:
                story_entity_id = EntityId.from_string(str(story_id))
                
                # Get story to check ownership
                async for session in get_database_session():
                    story_repo_inst = StoryRepositoryImpl(session)
                    story = await story_repo_inst.find_by_id(story_entity_id)
                    
                    if not story:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Story not found"
                        )
                    
                    user_id = current_user.get("sub")
                    if story.created_by.value != user_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to modify this story. Only the creator or an admin can modify stories."
                        )
                    break  # Exit after first iteration
                    
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid story ID format"
                )
        
        # Proceed with update
        result = await use_case.execute(
            story_id=str(story_id),
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            points=payload.points,
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        return result
    
    return await handler.execute(execute)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: DeleteStoryUseCase = Depends(get_delete_story_use_case),
) -> None:
    """
    Delete story.
    
    Requires authentication and authorization (story owner or admin).
    
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
    async def execute():
        # Authorization check: admin or story owner
        user_role = current_user.get("role")
        if user_role != UserRole.ADMIN.value:
            # Not admin - check if user is story owner
            from src.app.shared.presentation.dependencies import get_database_session
            from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
            
            try:
                story_entity_id = EntityId.from_string(str(story_id))
                
                # Get story to check ownership
                async for session in get_database_session():
                    story_repo_inst = StoryRepositoryImpl(session)
                    story = await story_repo_inst.find_by_id(story_entity_id)
                    
                    if not story:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Story not found"
                        )
                    
                    user_id = current_user.get("sub")
                    if story.created_by.value != user_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to delete this story. Only the creator or an admin can delete stories."
                        )
                    break  # Exit after first iteration
                    
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid story ID format"
                )
        
        # Proceed with delete
        deleted = await use_case.execute(str(story_id))
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
    
    await handler.execute(execute)


@router.post("/{story_id}/assign", response_model=StoryResponse)
async def assign_story(
    story_id: UUID,
    payload: AssignStoryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: AssignStoryUseCase = Depends(get_assign_story_use_case),
) -> StoryResponse:
    """
    Assign story to a user.
    
    Requires authentication.
    
    Args:
        story_id: Story UUID
        payload: AssignStoryRequest with user ID
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
    async def execute():
        result = await use_case.execute(
            story_id=str(story_id),
            user_id=payload.user_id,
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        return result
    
    return await handler.execute(execute)