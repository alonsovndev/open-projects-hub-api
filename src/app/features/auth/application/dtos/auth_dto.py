from datetime import UTC, datetime

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

    @classmethod
    def from_user_entity(cls, user_entity, token: str, refresh_token: str) -> "AdminLoginResponse":
        """
        Factory method to create response from UserEntity and tokens.

        Args:
            user_entity: UserEntity instance
            token: Generated JWT access token
            refresh_token: Generated JWT refresh token

        Returns:
            AdminLoginResponse instance
        """
        display_name = user_entity.display_name
        logged_in_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")

        return cls(
            token=token,
            access_token=token,
            refresh_token=refresh_token,
            email=str(user_entity.email),
            display_name=display_name,
            logged_in_at=logged_in_at,
            role=str(user_entity.role.value),
            user=UserDetail(
                email=str(user_entity.email),
                display_name=display_name,
                name=display_name,
                role=str(user_entity.role.value),
            ),
        )
