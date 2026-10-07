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


class EmailNotVerifiedError(AuthenticationError):
    """Raised on login when the password is correct but the account's email is unconfirmed.

    Only raised after the password check succeeds, so it reveals the account's state to
    nobody who doesn't already hold its credentials.
    """

    def __init__(self, message: str = "Please verify your email before signing in."):
        self.message = message
        super().__init__(self.message)


class InvalidVerificationCodeError(AuthenticationError):
    """Raised when a verification code is wrong, expired, superseded, or has no pending account.

    One error for every case, so the verify endpoint can't be used to learn which emails
    have accounts or which accounts are already verified.
    """

    def __init__(self, message: str = "Invalid or expired verification code"):
        self.message = message
        super().__init__(self.message)


class VerificationRateLimitedError(AuthenticationError):
    """Raised when verification-code resends or validation attempts exceed their limit."""

    def __init__(self, message: str = "Too many attempts. Please try again later."):
        self.message = message
        super().__init__(self.message)
