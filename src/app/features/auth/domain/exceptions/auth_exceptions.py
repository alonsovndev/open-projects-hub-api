class AuthenticationError(Exception):
    """Base exception for authentication errors."""


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


class AccountLockedError(AuthenticationError):
    """Raised when account is temporarily locked due to failed login attempts."""

    def __init__(
        self, message: str = "Account temporarily locked", remaining_seconds: int = 0, failed_attempts: int = 0
    ):
        self.message = message
        self.remaining_seconds = remaining_seconds
        self.failed_attempts = failed_attempts
        super().__init__(self.message)


class InvalidResetCodeError(AuthenticationError):
    """Raised when a password reset code is unknown, expired, or already used."""

    def __init__(self, message: str = "Invalid or expired reset code"):
        self.message = message
        super().__init__(self.message)


class ResetCodeRateLimitedError(AuthenticationError):
    """Raised when reset-code requests or validation attempts exceed their rate limit."""

    def __init__(self, message: str = "Too many attempts. Please try again later."):
        self.message = message
        super().__init__(self.message)


class RegistrationClosedError(AuthenticationError):
    """Raised when public registration is attempted after the instance already has a user.

    Registration exists to bootstrap the first Admin. Leaving it open afterwards would let
    any anonymous caller mint an Admin account and walk through every role boundary, so
    later accounts are created by an existing Admin through POST /v1/users.
    """

    def __init__(
        self,
        message: str = "Registration is closed. Ask an administrator to create your account.",
    ):
        self.message = message
        super().__init__(self.message)
