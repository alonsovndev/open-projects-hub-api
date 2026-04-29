class UserDoesNotExistException(Exception):
    """Exception raised when a user does not exist."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.message = f"User with ID {self.user_id} does not exist."
        super().__init__(self.message)

class UserAlreadyExistsException(Exception):
    """Exception raised when a user already exists (duplicate)."""

    def __init__(self, email: str):
        self.email = email
        self.message = f"User with email {self.email} already exists."
        super().__init__(self.message)
