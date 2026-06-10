"""Delete client use case."""

from uuid import UUID

from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.logging import BusinessLogger, get_logger


class DeleteClientUseCase:
    """Use case for deleting a client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: UUID, created_by: str) -> bool:
        """Execute the delete client use case.

        Args:
            client_id: UUID of the client to delete.
            created_by: User ID performing the deletion.

        Returns:
            bool: True if client was deleted, False if not found.

        Raises:
            ValueError: If client has associated projects (enforced by DB constraint).
        """
        log = BusinessLogger(get_logger(__name__), user_id=created_by)

        try:
            # Try to delete the client
            # If client has projects, the database RESTRICT constraint will raise an error
            deleted = await self.client_repository.delete(client_id)

            if not deleted:
                log.failure("client.delete.not_found", entity_id=str(client_id))
                raise ValueError(f"Client not found: {client_id}")

            log.event("client.deleted", entity_id=str(client_id))

            return True

        except ValueError:
            raise
        except Exception as e:
            log.failure("client.delete.unexpected_error", error=e, entity_id=str(client_id))
            raise
