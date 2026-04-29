from fastapi import APIRouter, Depends, HTTPException, status

from src.app.features.application.dtos.auth_dto import AdminLoginResponse, LoginRequest
from src.app.features.application.services.auth_service import AuthService
from src.app.features.domain.exceptions.auth_exceptions import InvalidCredentialsError
from src.app.features.presentation.web.dependencies import get_auth_service

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AdminLoginResponse:
    """
    Authenticate user and return JWT token with user details.

    Args:
        payload: LoginRequest with email and password

    Returns:
        AdminLoginResponse with token and user details

    Raises:
        401: Invalid credentials
    """
    try:
        response = await auth_service.login(payload)
        return response

    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
