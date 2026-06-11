from typing import Any
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.app.composition import (
    get_change_password_use_case,
    get_create_user_use_case,
    get_get_user_by_id_use_case,
    get_get_user_profile_use_case,
    get_update_user_profile_use_case,
)
from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.shared.presentation.auth_dependencies import get_current_user, require_admin


router = APIRouter()


# DTOs for new endpoints
class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    display_name: str


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    current_password: str
    new_password: str


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
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    get_user_use_case: GetUserByIdUseCase = Depends(get_get_user_by_id_use_case),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """
    Get user by ID.

    Requires authentication.

    Args:
        user_id: User UUID
        get_user_use_case: Injected GetUserByIdUseCase
        current_user: Current authenticated user

    Returns:
        UserResponse with user details (id, email, displayName, role)

    Raises:
        401: Unauthorized
        404: User not found
        500: Internal server error
    """
    return await get_user_use_case.execute(str(user_id))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    current_user: dict[str, Any] = Depends(require_admin),
) -> UserResponse:
    """
    Create a new user (admin only).

    Requires ADMIN role. For public self-registration, use POST /v1/auth/register instead.
    Admins can specify the role (admin or viewer) when creating users.
    Defaults to viewer if not specified.

    Args:
        payload: UserCreateRequest with email, password, displayName, optional role
        create_user_use_case: Injected CreateUserUseCase
        current_user: Current authenticated admin user

    Returns:
        UserResponse with created user data

    Raises:
        403: Forbidden (non-admin user)
        409: Conflict (email already exists)
        422: Validation error (invalid payload)
    """
    user_id = str(current_user["sub"])
    return await create_user_use_case.execute(payload, created_by=user_id)
