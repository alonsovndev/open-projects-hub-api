class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials"):
        self.message = message
        super().__init__(self.message)


class UnauthorizedError(AuthenticationError):
    """Raised when user is not authenticated."""

    def __init__(self, message: str = "Authentication required"):
        self.message = message
        super().__init__(self.message)


class InsufficientPermissionsError(AuthenticationError):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(self.message)


class AccountLockedError(AuthenticationError):
    """Raised when account is temporarily locked due to failed login attempts."""

    def __init__(
        self,
        message: str = "Account temporarily locked",
        remaining_seconds: int = 0,
        failed_attempts: int = 0
    ):
        self.message = message
        self.remaining_seconds = remaining_seconds
        self.failed_attempts = failed_attempts
        super().__init__(self.message)
