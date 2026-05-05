from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from src.app.features.application.dtos.user_dto import UserResponse, UserCreateRequest
from src.app.features.application.exceptions.user_exception import UserDoesNotExistException, UserAlreadyExistsException
from src.app.features.application.use_cases.create_user import CreateUserUseCase
from src.app.features.application.use_cases.get_user_by_id import GetUserByIdUseCase
from src.app.features.presentation.web.auth_dependencies import get_current_user, require_admin
from src.app.features.presentation.web.dependencies import get_create_user_use_case, get_user_by_id_use_case

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    get_user_use_case: GetUserByIdUseCase = Depends(get_user_by_id_use_case),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """
    Get user by ID.
    
    Requires authentication.
    
    Args:
        user_id: User UUID
        get_user_use_case: Injected use case (direct injection, no service layer)
        current_user: Current authenticated user
    """
    try:
        user_result = await get_user_use_case.execute(str(user_id))

        return user_result

    except UserDoesNotExistException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    current_user: Dict[str, Any] = Depends(require_admin),
) -> UserResponse:
    """
    Create a new user (admin only).
    
    Requires ADMIN role.
    
    Args:
        payload: User creation request
        create_user_use_case: Injected use case (direct injection, no service layer)
        current_user: Current authenticated admin user
    """
    try:
        user_result = await create_user_use_case.execute(payload)
        return user_result

    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
