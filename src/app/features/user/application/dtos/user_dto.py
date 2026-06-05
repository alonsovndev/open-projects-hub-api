from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.user.domain.validators.user_validators import UserValidators
from src.app.features.user.domain.value_objects.user_role import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str
    email: str
    display_name: str
    role: str


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    display_name: str
    email: EmailStr
    password: str
    role: str | None = "viewer"  # Default to viewer for public registration

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, display_name: str) -> str:
        """Validate display name."""
        UserValidators.validate_display_name(display_name)
        return display_name

    @field_validator("role")
    @classmethod
    def validate_role(cls, role: str | None) -> str:
        """
        Validate role is valid user role enum.

        Args:
            role: Role string

        Returns:
            The validated role in lowercase

        Raises:
            ValueError: If role is not valid
        """
        if role is None:
            return UserRole.VIEWER.value

        role_lower = role.lower().strip()
        valid_roles = [r.value for r in UserRole]
        if role_lower not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")

        return role_lower

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, password: str) -> str:
        """Validate password meets complexity requirements."""
        UserValidators.validate_password(password)
        return password
