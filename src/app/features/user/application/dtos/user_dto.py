from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.user.domain.validators.user_validators import UserValidators
from src.app.features.user.domain.value_objects.user_role import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    id: str
    email: str
    display_name: str
    role: str

class UserCreateRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    display_name: str
    email: EmailStr
    password: str
    role: Optional[str] = "viewer"  # Default to viewer for public registration

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Validate display name."""
        UserValidators.validate_display_name(v)
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> str:
        """
        Validate role is valid user role enum.
        
        Args:
            v: Role string
            
        Returns:
            The validated role in lowercase
            
        Raises:
            ValueError: If role is not valid
        """
        if v is None:
            return UserRole.VIEWER.value
        
        role_lower = v.lower().strip()
        valid_roles = [r.value for r in UserRole]
        if role_lower not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        
        return role_lower

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        UserValidators.validate_password(v)
        return v

