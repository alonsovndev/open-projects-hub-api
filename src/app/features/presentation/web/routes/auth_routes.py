from fastapi import APIRouter, Depends, HTTPException, status, Request

from src.app.features.application.dtos.auth_dto import AdminLoginResponse, LoginRequest
from src.app.features.application.use_cases.login_user import LoginUserUseCase
from src.app.features.domain.exceptions.auth_exceptions import InvalidCredentialsError
from src.app.features.presentation.web.dependencies import get_login_use_case
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    payload: LoginRequest,
    login_use_case: LoginUserUseCase = Depends(get_login_use_case),
) -> AdminLoginResponse:
    """
    Authenticate user and return JWT token with user details.
    
    Rate limited to 5 attempts per 15 minutes per IP address to prevent brute force attacks.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: LoginRequest with email and password
        login_use_case: Injected LoginUserUseCase (direct injection, no service layer)

    Returns:
        AdminLoginResponse with token and user details

    Raises:
        401: Invalid credentials
        429: Too many requests (rate limit exceeded)
        500: Internal server error
    """
    try:
        response = await login_use_case.execute(payload)
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

