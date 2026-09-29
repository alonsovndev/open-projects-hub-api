from enum import StrEnum


class UserRole(StrEnum):
    """
    Enumeration of user roles in the system.
    Inherits from str to ensure JSON serialization compatibility.

    Values are lowercase to match API contract requirements.
    """

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def default(cls) -> "UserRole":
        """Return the default role for new users."""
        return cls.VIEWER
