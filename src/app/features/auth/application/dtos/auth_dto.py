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
    email: str
    display_name: str
    logged_in_at: str
    role: str
    user: UserDetail
