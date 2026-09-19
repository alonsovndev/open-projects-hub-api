"""Domain exceptions for user feature."""


class UserNotFoundError(Exception):
    """Raised when a user cannot be found."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")


class UserAlreadyExistsError(Exception):
    """Raised when a user already exists (duplicate email)."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' already exists")
