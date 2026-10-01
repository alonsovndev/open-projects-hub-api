from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.user.domain.validators.user_validators import UserValidators
from src.app.features.user.domain.value_objects.user_role import UserRole


def _validate_assignable_role(role: str | None) -> str:
    """
    Only teammates and viewers can be given to someone in a workspace.

    A workspace has exactly one Admin, so Admin is never assignable.

    Raises:
        ValueError: If role is not member or viewer
    """
    if role is None:
        return UserRole.MEMBER.value

    role_lower = role.lower().strip()
    assignable_roles = [UserRole.MEMBER.value, UserRole.VIEWER.value]
    if role_lower not in assignable_roles:
        raise ValueError(f"Role must be one of: {', '.join(assignable_roles)}")

    return role_lower


class UserResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str
    email: str
    display_name: str
    role: str
    is_active: bool = True


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    display_name: str
    email: EmailStr
    password: str
    role: str | None = UserRole.MEMBER.value

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, display_name: str) -> str:
        """Validate display name."""
        UserValidators.validate_display_name(display_name)
        return display_name

    @field_validator("role")
    @classmethod
    def validate_role(cls, role: str | None) -> str:
        return _validate_assignable_role(role)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, password: str) -> str:
        """Validate password meets complexity requirements."""
        UserValidators.validate_password(password)
        return password


class UpdateUserRoleRequest(BaseModel):
    """Request model for an Admin changing a teammate's role."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, role: str) -> str:
        return _validate_assignable_role(role)


class UpdateUserStatusRequest(BaseModel):
    """Request model for an Admin activating or deactivating a teammate."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    active: bool


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    display_name: str


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    current_password: str
    new_password: str
