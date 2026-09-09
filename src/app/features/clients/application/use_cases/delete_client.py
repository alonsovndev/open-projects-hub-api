"""Delete client use case."""

from uuid import UUID

from src.app.features.clients.domain.exceptions.client_exceptions import ClientNotFoundError
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.logging import get_logger, set_user_id


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
        log = get_logger(__name__)
        set_user_id(created_by)

        try:
            # Try to delete the client
            # If client has projects, the database RESTRICT constraint will raise an error
            deleted = await self.client_repository.delete(client_id)

            if not deleted:
                log.error(
                    "Client not found for deletion",
                    extra={"event_type": "client.delete.not_found", "entity_id": str(client_id)},
                )
                raise ClientNotFoundError(str(client_id))

            log.info("Client deleted", extra={"event_type": "client.deleted", "entity_id": str(client_id)})

            return True

        except (ClientNotFoundError, ValueError):
            raise
        except Exception:
            log.exception(
                "Unexpected error deleting client",
                extra={"event_type": "client.delete.unexpected_error", "entity_id": str(client_id)},
            )
            raise
