from enum import Enum


class UserRole(str, Enum):
    """
    Enumeration of user roles in the system.
    Inherits from str to ensure JSON serialization compatibility.

    Values are lowercase to match API contract requirements.
    """

    ADMIN = "admin"
    VIEWER = "viewer"

    def __str__(self) -> str:
        return self.value
