from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel


class LoginRequest(BaseModel):
    """Request model for user login."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: EmailStr
    password: str
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    access_token: str
    refresh_token: str
    session_expires_at: str


class UserDetail(BaseModel):
    """Nested user details in login response."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: str
    display_name: str
    name: str
    role: str


class AdminLoginResponse(BaseModel):
    """
    Response model for admin login.
    Matches frontend AdminLoginApiResponse interface.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    token: str
    access_token: str
    refresh_token: str
    session_expires_at: str
    email: str
    display_name: str
    logged_in_at: str
    role: str
    user: UserDetail


class LogoutResponse(BaseModel):
    """Response model for logout."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    message: str


class ForgotPasswordRequest(BaseModel):
    """Request model for initiating a password reset."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """
    Response model for a password reset request.

    Always returns the same generic message regardless of whether the email
    is registered, so the endpoint never discloses account existence.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    message: str


class ResendResetCodeRequest(BaseModel):
    """Request model for resending a password reset code."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for completing a password reset."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: EmailStr
    code: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    """Response model for a completed password reset."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    message: str
