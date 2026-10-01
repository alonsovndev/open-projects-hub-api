from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.user.domain.validators.user_validators import UserValidators
from src.app.features.workspaces.domain.entities.workspace_entity import WORKSPACE_NAME_MAX_LENGTH


class RegisterRequest(BaseModel):
    """
    Request model for public self-registration.

    Deliberately has no `role` field: registration is anonymous, so a role taken from the
    request body would let anyone mint an Admin account. The role is assigned server-side.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    display_name: str
    email: EmailStr
    password: str
    workspace_name: str | None = Field(default=None, max_length=WORKSPACE_NAME_MAX_LENGTH)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, display_name: str) -> str:
        """Validate display name."""
        UserValidators.validate_display_name(display_name)
        return display_name

    @field_validator("workspace_name")
    @classmethod
    def blank_workspace_name_means_default(cls, workspace_name: str | None) -> str | None:
        """An empty or whitespace-only name falls back to the default derived from the display name."""
        if workspace_name is None:
            return None
        return workspace_name.strip() or None

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, password: str) -> str:
        """Validate password meets complexity requirements."""
        UserValidators.validate_password(password)
        return password


class RegisterResponse(BaseModel):
    """
    Response model for a registration awaiting email verification.

    Carries no tokens: the account cannot sign in until its email is verified (FR-008-06).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: str
    verification_required: bool = True
    next_step: str = "verify-email"
    code_expires_at: str


class VerifyEmailRequest(BaseModel):
    """Request model for confirming an account's email with its verification code."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: EmailStr
    # Bounded so oversized input is rejected before it reaches bcrypt; the slack over 6
    # allows surrounding whitespace, which the use case strips.
    code: str = Field(min_length=6, max_length=16)
    # Invited accounts choose their password here; self-registered ones already did.
    password: str | None = Field(default=None, max_length=72)


class VerifyEmailResponse(BaseModel):
    """Response model for a verified email."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    verified: bool = True


class ResendVerificationRequest(BaseModel):
    """Request model for resending an email verification code."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    email: EmailStr


class ResendVerificationResponse(BaseModel):
    """
    Response model for a verification code resend.

    Always the same generic message, so the endpoint never discloses whether the email
    belongs to a pending account.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    message: str


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


class WorkspaceDetail(BaseModel):
    """The workspace the signed-in user belongs to."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    name: str


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
    workspace: WorkspaceDetail | None = None


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
