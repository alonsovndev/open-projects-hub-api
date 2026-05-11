import re
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic.alias_generators import to_camel


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

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Validate password meets complexity requirements:
        - At least 8 characters
        - At least one letter
        - At least one digit
        
        Args:
            v: Password string
            
        Returns:
            The validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        
        return v

