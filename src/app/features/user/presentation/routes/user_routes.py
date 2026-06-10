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
from src.app.features.auth.presentation.auth_dependencies import get_current_user, require_admin
from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.application.exceptions.user_exception import (
    UserAlreadyExistsException,
    UserDoesNotExistException,
    UserNotFoundException,
)
from src.app.features.user.application.use_cases.change_password import ChangePasswordUseCase
from src.app.features.user.application.use_cases.create_user import CreateUserUseCase
from src.app.features.user.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.user.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.app.features.user.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.app.shared.presentation.base_handler import BaseRouteHandler, ExceptionMapping


router = APIRouter()
handler = BaseRouteHandler()

# Common exception mappings for user routes
USER_EXCEPTION_MAPPINGS = [
    ExceptionMapping(UserNotFoundException, status.HTTP_404_NOT_FOUND),
    ExceptionMapping(UserDoesNotExistException, status.HTTP_404_NOT_FOUND),
    ExceptionMapping(UserAlreadyExistsException, status.HTTP_409_CONFLICT),
    ExceptionMapping(ValueError, status.HTTP_400_BAD_REQUEST),
]


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

    Requires authentication. Returns profile for the authenticated user from JWT token.

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
    return await handler.execute_with_payload_extraction(  # type: ignore[no-any-return]
        execute_fn=lambda user_id: use_case.execute(user_id),
        current_user=current_user,
        exception_mappings=USER_EXCEPTION_MAPPINGS,
    )


@router.patch("/me/profile", response_model=UserResponse)
async def update_user_profile(
    payload: UpdateProfileRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: UpdateUserProfileUseCase = Depends(get_update_user_profile_use_case),
) -> UserResponse:
    """
    Update current user profile.

    Requires authentication. Only display_name can be updated.
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
    return await handler.execute_with_payload_extraction(  # type: ignore[no-any-return]
        execute_fn=lambda user_id: use_case.execute(user_id, payload.display_name),
        current_user=current_user,
        exception_mappings=USER_EXCEPTION_MAPPINGS,
    )


@router.post("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: ChangePasswordUseCase = Depends(get_change_password_use_case),
) -> dict[str, str]:
    """
    Change user password.

    Requires authentication. Verifies current password before updating to new password.
    New password must meet complexity requirements (min 8 chars, letter + digit).

    Args:
        payload: ChangePasswordRequest with currentPassword and newPassword
        current_user: Current authenticated user (from JWT)
        use_case: Injected ChangePasswordUseCase

    Returns:
        Success message

    Raises:
        400: Validation failed (weak password, incorrect current password)
        401: Unauthorized (invalid or missing token)
        404: User not found
        500: Internal server error
    """

    async def execute(user_id: str):
        await use_case.execute(
            user_id=user_id, current_password=payload.current_password, new_password=payload.new_password
        )
        return {"message": "Password changed successfully"}

    return await handler.execute_with_payload_extraction(  # type: ignore[no-any-return]
        execute_fn=execute,
        current_user=current_user,
        exception_mappings=USER_EXCEPTION_MAPPINGS,
    )


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
        get_user_use_case: Injected use case (direct injection, no service layer)
        current_user: Current authenticated user
    """

    async def execute():
        return await get_user_use_case.execute(str(user_id))

    return await handler.execute(execute, exception_mappings=USER_EXCEPTION_MAPPINGS)  # type: ignore[no-any-return]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    current_user: dict[str, Any] = Depends(require_admin),
) -> UserResponse:
    """
    Create a new user (admin only).

    Standard REST endpoint: POST /v1/users
    Requires ADMIN role. For public self-registration, use POST /v1/auth/register instead.

    Admins can specify the role ('admin' or 'viewer') when creating users.
    If role is not specified, defaults to 'viewer'.

    Args:
        payload: User creation request (email, password, displayName, optional role)
        create_user_use_case: Injected use case (direct injection, no service layer)
        current_user: Current authenticated admin user

    Returns:
        UserResponse with created user data

    Raises:
        403: Forbidden (non-admin user)
        409: Conflict (email already exists)
        422: Validation error (invalid payload)
    """

    async def execute():
        user_id = str(current_user["sub"])
        return await create_user_use_case.execute(payload, created_by=user_id)

    return await handler.execute(execute, exception_mappings=USER_EXCEPTION_MAPPINGS)  # type: ignore[no-any-return]
