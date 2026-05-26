from fastapi import APIRouter, Depends, status, Request
import jwt

from src.app.features.auth.application.dtos.auth_dto import AdminLoginResponse, LoginRequest
from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.auth.application.use_cases.refresh_token import (
    RefreshTokenUseCase,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from src.app.features.auth.domain.exceptions.auth_exceptions import InvalidCredentialsError
from src.app.features.auth.presentation.dependencies import (
    get_login_use_case,
    get_register_use_case,
    get_refresh_token_use_case,
)
from src.app.features.user.application.dtos.user_dto import UserCreateRequest
from src.app.features.user.application.exceptions.user_exception import UserAlreadyExistsException
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.presentation.base_handler import BaseRouteHandler, ExceptionMapping

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    login_use_case: LoginUserUseCase = Depends(get_login_use_case),
) -> AdminLoginResponse:
    """
    Authenticate user and return JWT token with user details.
    
    Rate limited to 10 attempts per minute per IP address to prevent brute force attacks.

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
    return await BaseRouteHandler.execute(
        login_use_case.execute,
        payload=payload,
        exception_mappings=[
            ExceptionMapping(InvalidCredentialsError, status.HTTP_401_UNAUTHORIZED),
        ],
    )


@router.post("/register", response_model=AdminLoginResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: UserCreateRequest,
    register_use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> AdminLoginResponse:
    """
    Register new user and return JWT token (auto-login).
    
    Rate limited to 5 attempts per minute per IP address to prevent abuse.
    
    Public endpoint - no authentication required.
    New users default to 'viewer' role. To create admin users, 
    use POST /v1/users (requires existing admin authentication).

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: UserCreateRequest with email, password, displayName (role defaults to viewer)
        register_use_case: Injected RegisterUserUseCase

    Returns:
        AdminLoginResponse with JWT token and user details

    Raises:
        400: Validation failed (weak password, invalid email, etc.)
        409: Email already exists
        500: Internal server error
    """
    return await BaseRouteHandler.execute(
        register_use_case.execute,
        payload=payload,
        exception_mappings=[
            ExceptionMapping(UserAlreadyExistsException, status.HTTP_409_CONFLICT),
            ExceptionMapping(ValueError, status.HTTP_400_BAD_REQUEST, extract_message=False),
        ],
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
@limiter.limit("10/15minutes")
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    refresh_use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token.
    
    Implements single-use refresh token rotation:
    - Returns new access token (15min TTL) AND new refresh token (7 days)
    - Old refresh token is immediately revoked and cannot be reused
    - Prevents token replay attacks
    
    Rate limited to 10 attempts per 15 minutes per IP address.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: RefreshTokenRequest with refresh token
        refresh_use_case: Injected RefreshTokenUseCase

    Returns:
        RefreshTokenResponse with new access and refresh tokens

    Raises:
        401: Refresh token expired or invalid
        429: Too many requests (rate limit exceeded)
        500: Internal server error
    """
    return await BaseRouteHandler.execute(
        refresh_use_case.execute,
        payload=payload,
        exception_mappings=[
            ExceptionMapping(
                jwt.ExpiredSignatureError,
                status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            ),
            ExceptionMapping(
                jwt.InvalidTokenError,
                status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ),
            ExceptionMapping(
                ValueError,
                status.HTTP_401_UNAUTHORIZED,
                extract_message=False,
            ),
        ],
    )
