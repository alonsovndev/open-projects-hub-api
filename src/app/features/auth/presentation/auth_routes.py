import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.app.composition import (
    get_confirm_password_reset_use_case,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_token_use_case,
    get_register_use_case,
    get_request_password_reset_use_case,
    get_resend_reset_code_use_case,
)
from src.app.features.auth.application.dtos.auth_dto import (
    AdminLoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    ResendResetCodeRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from src.app.features.auth.application.use_cases.confirm_password_reset import ConfirmPasswordResetUseCase
from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.application.use_cases.logout_user import LogoutUseCase
from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.auth.application.use_cases.request_password_reset import RequestPasswordResetUseCase
from src.app.features.auth.application.use_cases.resend_reset_code import ResendResetCodeUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    InvalidResetCodeError,
    ResetCodeRateLimitedError,
)
from src.app.features.user.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.presentation.auth_dependencies import get_current_user


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
        login_use_case: Injected LoginUserUseCase

    Returns:
        AdminLoginResponse with JWT token and user details

    Raises:
        401: Invalid credentials
        429: Too many requests (rate limit exceeded)
        500: Internal server error
    """
    try:
        return await login_use_case.execute(payload=payload)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/register", response_model=AdminLoginResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    register_use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> AdminLoginResponse:
    """
    Register new admin account and return JWT token (auto-login).

    Rate limited to 5 attempts per minute per IP address to prevent abuse.

    Public endpoint - no authentication required. The account is always created with the
    Admin role; a role supplied in the request body is rejected. Viewer accounts are
    created by an existing admin through POST /v1/users.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: RegisterRequest with email, password, displayName
        register_use_case: Injected RegisterUserUseCase

    Returns:
        AdminLoginResponse with JWT token and user details

    Raises:
        400: Validation failed (weak password, invalid email, etc.)
        409: Email already exists
        422: Unknown field in the request body (for example an attempted role override)
        500: Internal server error
    """
    try:
        return await register_use_case.execute(payload=payload)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


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
    try:
        return await refresh_use_case.execute(payload=payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    payload: RefreshTokenRequest,
    _current_user: dict = Depends(get_current_user),
    logout_use_case: LogoutUseCase = Depends(get_logout_use_case),
) -> LogoutResponse:
    """
    Log out the current session by revoking its refresh token server-side.

    Requires a valid access token (Authorization header) plus the session's
    refresh token in the body. Idempotent: an already-expired/invalid
    refresh token still returns success rather than an error.

    Args:
        payload: RefreshTokenRequest with the session's refresh token
        logout_use_case: Injected LogoutUseCase

    Returns:
        LogoutResponse confirming the session was invalidated
    """
    return await logout_use_case.execute(payload=payload)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/15minutes")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    use_case: RequestPasswordResetUseCase = Depends(get_request_password_reset_use_case),
) -> ForgotPasswordResponse:
    """
    Request a password reset code by email.

    Always returns 200 with the same generic message, whether or not the
    email is registered, to avoid disclosing account existence.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: ForgotPasswordRequest with the account email
        use_case: Injected RequestPasswordResetUseCase

    Returns:
        ForgotPasswordResponse with a generic confirmation message
    """
    return await use_case.execute(payload=payload)


@router.post("/resend-reset-code", response_model=ForgotPasswordResponse)
@limiter.limit("5/15minutes")
async def resend_reset_code(
    request: Request,
    payload: ResendResetCodeRequest,
    use_case: ResendResetCodeUseCase = Depends(get_resend_reset_code_use_case),
) -> ForgotPasswordResponse:
    """
    Resend a password reset code, invalidating the previous one.

    Rate limited to 3 resends per email per 15-minute window (enforced in
    ResendResetCodeUseCase); the route-level limiter above is a coarser
    per-IP backstop.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: ResendResetCodeRequest with the account email
        use_case: Injected ResendResetCodeUseCase

    Returns:
        ForgotPasswordResponse with a generic confirmation message

    Raises:
        429: Resend limit exceeded for this email
    """
    try:
        return await use_case.execute(payload=payload)
    except ResetCodeRateLimitedError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)) from e


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("10/15minutes")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    use_case: ConfirmPasswordResetUseCase = Depends(get_confirm_password_reset_use_case),
) -> ResetPasswordResponse:
    """
    Complete a password reset using a previously issued code.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: ResetPasswordRequest with email, code, and new password
        use_case: Injected ConfirmPasswordResetUseCase

    Returns:
        ResetPasswordResponse confirming the password was changed

    Raises:
        400: New password fails validation
        404: Reset code invalid or expired
        429: Too many validation attempts against this code
    """
    try:
        return await use_case.execute(payload=payload)
    except InvalidResetCodeError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ResetCodeRateLimitedError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
