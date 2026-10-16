import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials

from src.app.composition import (
    get_confirm_password_reset_use_case,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_token_use_case,
    get_register_use_case,
    get_request_password_reset_use_case,
    get_resend_reset_code_use_case,
    get_resend_verification_use_case,
    get_verify_email_use_case,
)
from src.app.composition.infrastructure import get_jwt_handler
from src.app.features.auth.application.dtos.auth_dto import (
    AdminLoginResponse,
    BrowserSessionResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    ResendResetCodeRequest,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from src.app.features.auth.application.mappers.auth_mapper import to_browser_session_response
from src.app.features.auth.application.use_cases.confirm_password_reset import ConfirmPasswordResetUseCase
from src.app.features.auth.application.use_cases.login_user import LoginUserUseCase
from src.app.features.auth.application.use_cases.logout_user import LogoutUseCase
from src.app.features.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from src.app.features.auth.application.use_cases.register_user import RegisterUserUseCase
from src.app.features.auth.application.use_cases.request_password_reset import RequestPasswordResetUseCase
from src.app.features.auth.application.use_cases.resend_reset_code import ResendResetCodeUseCase
from src.app.features.auth.application.use_cases.resend_verification import ResendVerificationUseCase
from src.app.features.auth.application.use_cases.verify_email import VerifyEmailUseCase
from src.app.features.auth.domain.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    InvalidResetCodeError,
    InvalidVerificationCodeError,
    ResetCodeRateLimitedError,
    VerificationRateLimitedError,
)
from src.app.features.auth.presentation.browser_session import (
    BROWSER_SESSION_OPENAPI,
    REFRESH_COOKIE,
    clear_refresh_cookie,
    is_browser_session,
    refresh_request,
    set_refresh_cookie,
)
from src.app.shared.infrastructure.rate_limit.rate_limiter import limiter
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.presentation.auth_dependencies import get_current_user, security


router = APIRouter()


@router.post(
    "/login", response_model=AdminLoginResponse | BrowserSessionResponse, openapi_extra=BROWSER_SESSION_OPENAPI
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    login_use_case: LoginUserUseCase = Depends(get_login_use_case),
) -> AdminLoginResponse | BrowserSessionResponse:
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
        403: Email not verified yet (body carries code EMAIL_NOT_VERIFIED)
        429: Too many requests (rate limit exceeded)
        500: Internal server error
    """
    browser_mode = is_browser_session(request)
    try:
        session = await login_use_case.execute(payload=payload)
        if browser_mode:
            set_refresh_cookie(response, session.refresh_token, jwt_handler)
            return to_browser_session_response(session)
        return session
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    register_use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> RegisterResponse:
    """
    Register new admin account and email it a verification code.

    No tokens are issued: the account signs in only after POST /verify-email succeeds.

    Rate limited to 5 attempts per minute per IP address to prevent abuse.

    Public endpoint - no authentication required. Each sign-up creates a new, empty
    workspace and makes the account its Admin; a role supplied in the request body is
    rejected. Teammates are added to a workspace by its Admin through
    POST /v1/users.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: RegisterRequest with email, password, displayName, optional workspaceName
        register_use_case: Injected RegisterUserUseCase

    Returns:
        RegisterResponse with the masked email and when the verification code expires

    Raises:
        400: Validation failed (weak password, invalid email, etc.)
        422: Unknown field in the request body (for example an attempted role override)
        500: Internal server error
    """
    return await register_use_case.execute(payload=payload)


@router.post("/verify-email", response_model=VerifyEmailResponse)
@limiter.limit("10/15minutes")
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    use_case: VerifyEmailUseCase = Depends(get_verify_email_use_case),
) -> VerifyEmailResponse:
    """
    Confirm a registered account's email with the code it was sent.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: VerifyEmailRequest with the account email and code
        use_case: Injected VerifyEmailUseCase

    Returns:
        VerifyEmailResponse confirming the email was verified

    Raises:
        400: Code invalid, expired, or superseded
        429: Too many validation attempts against this code
    """
    try:
        return await use_case.execute(payload=payload)
    except InvalidVerificationCodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except VerificationRateLimitedError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)) from e


@router.post("/resend-verification", response_model=ResendVerificationResponse)
@limiter.limit("5/15minutes")
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    use_case: ResendVerificationUseCase = Depends(get_resend_verification_use_case),
) -> ResendVerificationResponse:
    """
    Resend an email verification code, invalidating the previous one.

    Rate limited to 3 resends per email per 15-minute window (enforced in
    ResendVerificationUseCase); the route-level limiter above is a coarser
    per-IP backstop.

    Args:
        request: FastAPI request object (required for rate limiting)
        payload: ResendVerificationRequest with the account email
        use_case: Injected ResendVerificationUseCase

    Returns:
        ResendVerificationResponse with a generic confirmation message

    Raises:
        429: Resend limit exceeded for this email
    """
    try:
        return await use_case.execute(payload=payload)
    except VerificationRateLimitedError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)) from e


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse | BrowserSessionResponse,
    response_model_exclude_none=True,
    openapi_extra=BROWSER_SESSION_OPENAPI,
)
@limiter.limit("10/15minutes")
async def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    refresh_use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> RefreshTokenResponse | BrowserSessionResponse:
    browser_mode = is_browser_session(request)
    token_request = refresh_request(request, payload)
    try:
        session = await refresh_use_case.execute(payload=token_request)
        if browser_mode:
            if session.user is None:
                raise HTTPException(status_code=500, detail="Session identity is unavailable")
            set_refresh_cookie(response, session.refresh_token, jwt_handler)
            return to_browser_session_response(session)
        return session
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError) as error:
        headers = None
        if browser_mode:
            clear_refresh_cookie(response)
            headers = {"Set-Cookie": response.headers["set-cookie"]}
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token", headers=headers) from error


async def logout_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> dict | None:
    if is_browser_session(request):
        return None
    return await get_current_user(request, credentials, jwt_handler)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    openapi_extra={**BROWSER_SESSION_OPENAPI, "security": [{"HTTPBearer": []}, {}]},
)
async def logout(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    _current_user: dict | None = Depends(logout_principal),
    logout_use_case: LogoutUseCase = Depends(get_logout_use_case),
) -> LogoutResponse:
    browser_mode = is_browser_session(request)
    if browser_mode and not request.cookies.get(REFRESH_COOKIE):
        if payload is not None:
            raise HTTPException(status_code=422, detail="Cookie sessions do not accept body credentials")
        clear_refresh_cookie(response)
        return LogoutResponse(message="Logged out successfully.")
    token_request = refresh_request(request, payload)
    result = await logout_use_case.execute(payload=token_request)
    if browser_mode:
        clear_refresh_cookie(response)
    return result


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
