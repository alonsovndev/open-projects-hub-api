from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.params import Depends

from src.app.composition import (
    get_change_password_use_case,
    get_create_user_use_case,
    get_delete_user_use_case,
    get_get_user_by_id_use_case,
    get_get_user_profile_use_case,
    get_list_workspace_users_use_case,
    get_update_user_profile_use_case,
    get_update_user_role_use_case,
    get_update_user_status_use_case,
)
from src.app.features.user.application.dtos.user_dto import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
    UserCreateRequest,
    UserResponse,
)
from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.application.use_cases.delete_user import DeleteUserUseCase
from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.application.use_cases.list_workspace_users import ListWorkspaceUsersUseCase
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.features.user.application.use_cases.update_user_role import UpdateUserRoleUseCase
from src.app.features.user.application.use_cases.update_user_status import UpdateUserStatusUseCase
from src.app.shared.application.request_context import RequestContext
from src.app.shared.presentation.auth_dependencies import (
    get_current_user,
    get_request_context,
    require_admin,
    require_editor,
)


router = APIRouter()


# Profile endpoints (must come before /{user_id} to avoid path conflicts)
@router.get("/me/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: GetUserProfileUseCase = Depends(get_get_user_profile_use_case),
) -> UserResponse:
    """
    Get current user profile.

    Requires authentication. Returns profile for the authenticated user from the JWT token.

    Args:
        current_user: Current authenticated user (from JWT)
        use_case: Injected GetUserProfileUseCase

    Returns:
        UserResponse with profile data (id, email, displayName, role)

    Raises:
        401: Unauthorized (invalid or missing token)
        404: User not found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    return await use_case.execute(user_id)


@router.patch("/me/profile", response_model=UserResponse)
async def update_user_profile(
    payload: UpdateProfileRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: UpdateUserProfileUseCase = Depends(get_update_user_profile_use_case),
) -> UserResponse:
    """
    Update current user profile.

    Requires authentication. Only the display_name field can be updated.
    Email and role cannot be changed via this endpoint.

    Args:
        payload: UpdateProfileRequest with displayName
        current_user: Current authenticated user (from JWT)
        use_case: Injected UpdateUserProfileUseCase

    Returns:
        UserResponse with updated profile data

    Raises:
        400: Validation failed (empty name, too long, etc.)
        401: Unauthorized (invalid or missing token)
        404: User not found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    return await use_case.execute(user_id, payload.display_name)


@router.post("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: ChangePasswordUseCase = Depends(get_change_password_use_case),
) -> dict[str, str]:
    """
    Change user password.

    Requires authentication. Verifies the current password before updating
    to the new password. New password must meet complexity requirements.

    Args:
        payload: ChangePasswordRequest with currentPassword and newPassword
        current_user: Current authenticated user (from JWT)
        use_case: Injected ChangePasswordUseCase

    Returns:
        Success message confirming password change

    Raises:
        400: Validation failed (weak password, incorrect current password)
        401: Unauthorized (invalid or missing token)
        404: User not found
        500: Internal server error
    """
    user_id = str(current_user["sub"])
    await use_case.execute(
        user_id=user_id, current_password=payload.current_password, new_password=payload.new_password
    )
    return {"message": "Password changed successfully"}


# Generic user endpoints
@router.get("", response_model=list[UserResponse])
async def list_workspace_users(
    ctx: RequestContext = Depends(require_editor),
    use_case: ListWorkspaceUsersUseCase = Depends(get_list_workspace_users_use_case),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[UserResponse]:
    """
    List the users of the caller's workspace (Admin and Member).

    Raises:
        401: Unauthorized
        403: Forbidden (viewer)
    """
    return await use_case.execute(ctx, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    get_user_use_case: GetUserByIdUseCase = Depends(get_get_user_by_id_use_case),
    ctx: RequestContext = Depends(get_request_context),
) -> UserResponse:
    """
    Get a user of the caller's workspace by ID.

    A Viewer may fetch only their own account. Users of other workspaces answer 404.

    Raises:
        401: Unauthorized
        404: User not found (or not visible to the caller)
    """
    return await get_user_use_case.execute(str(user_id), ctx)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    ctx: RequestContext = Depends(require_admin),
) -> UserResponse:
    """
    Add a member or viewer to the caller's workspace (Admin only).

    The account is created verified, with no free platform credits. Creating another Admin
    is refused (422). For self sign-up, use POST /v1/auth/register instead.

    Raises:
        403: Forbidden (non-admin user)
        409: Conflict (email already exists)
        422: Validation error (invalid payload or role)
    """
    return await create_user_use_case.execute(payload, ctx)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    payload: UpdateUserRoleRequest,
    use_case: UpdateUserRoleUseCase = Depends(get_update_user_role_use_case),
    ctx: RequestContext = Depends(require_admin),
) -> UserResponse:
    """
    Change a teammate's role between member and viewer (Admin only).

    The workspace Admin's role cannot be changed and nobody can be made Admin. The person's
    refresh tokens are revoked, so the new role applies once their current access token expires.

    Raises:
        400: Target is the Admin
        403: Forbidden (non-admin caller)
        404: User not found (or in another workspace)
        422: Role is not member or viewer
    """
    return await use_case.execute(str(user_id), payload.role, ctx)


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: UUID,
    payload: UpdateUserStatusRequest,
    use_case: UpdateUserStatusUseCase = Depends(get_update_user_status_use_case),
    ctx: RequestContext = Depends(require_admin),
) -> UserResponse:
    """
    Activate or deactivate a teammate (Admin only).

    An inactive account stays in the team list but cannot sign in, refresh a session or be
    assigned stories. An access token already issued works until it expires.

    Raises:
        400: Target is the Admin
        403: Forbidden (non-admin caller)
        404: User not found (or in another workspace)
    """
    return await use_case.execute(str(user_id), payload.active, ctx)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
    ctx: RequestContext = Depends(require_admin),
) -> None:
    """
    Permanently delete a teammate (Admin only).

    Projects and stories they created, and stories assigned to them, move to the calling
    Admin. Their stored AI keys are erased. This cannot be undone.

    Raises:
        400: Target is the Admin
        403: Forbidden (non-admin caller)
        404: User not found (or in another workspace)
    """
    await use_case.execute(str(user_id), ctx)
