"""Domain exceptions for clients feature."""


class ClientNotFoundError(Exception):
    """Raised when a client cannot be found."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        super().__init__(f"Client not found: {client_id}")


class ClientEmailExistsError(Exception):
    """Raised when attempting to create/update a client with a duplicate email."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Client with email {email} already exists")


class ClientHasActiveProjectsError(Exception):
    """Raised when attempting to delete a client that still has active projects."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        super().__init__(f"Client {client_id} has active projects and cannot be deleted")
