from enum import Enum


class UserRole(str, Enum):
    """
    Enumeration of user roles in the system.
    Inherits from str to ensure JSON serialization compatibility.
    """

    ADMIN = "ADMIN"
    USER = "USER"

    def __str__(self) -> str:
        return self.value
