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


class AICreditsExhaustedError(Exception):
    """
    Raised when a platform refinement is attempted with no free credits left.

    Lives with the user aggregate because the credit balance is a property of the account.
    The ai_config and refinement features both raise it; maps to HTTP 402, which the API
    contract reserves for exactly this case.
    """

    def __init__(self) -> None:
        super().__init__("No AI credits remaining. Add your own API key to continue unlimited refinements.")
