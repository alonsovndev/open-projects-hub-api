from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from src.app.features.application.dtos.user_dto import UserResponse, UserCreateRequest
from src.app.features.application.exceptions.user_exception import UserDoesNotExistException, UserAlreadyExistsException
from src.app.features.application.services.user_service import UserService
from src.app.features.presentation.web.dependencies import get_user_service

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: UUID, user_service: UserService = Depends(get_user_service)) -> UserResponse:
    # """
    # Get a user by their ID.
    #
    # Args:
    #     user_id (UUID): The user's unique identifier.
    #
    # Returns:
    #     UserResponse: The user's details.
    # """

    try:
        user_result = await user_service.get_user_by_id(str(user_id))

        return user_result

    except UserDoesNotExistException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreateRequest, user_service: UserService = Depends(get_user_service)) -> UserResponse:
    # """
    # Create a new user.
    #
    # Returns:
    #     Returns the created user details including the generated ID.
    #     Validates email uniqueness and securely hashes the password.
    # """

    try:
        user_result = await user_service.create_user(payload)
        return user_result

    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")