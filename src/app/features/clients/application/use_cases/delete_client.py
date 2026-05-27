"""Delete client use case."""

from uuid import UUID

from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.logging import get_logger, log_business_event, log_error_event


log = get_logger(__name__)


class DeleteClientUseCase:
    """Use case for deleting a client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: UUID) -> bool:
        """Execute the delete client use case.

        Returns:
            bool: True if client was deleted, False if not found.

        Raises:
            ValueError: If client has associated projects (enforced by DB constraint).
        """
        try:
            # Try to delete the client
            # If client has projects, the database RESTRICT constraint will raise an error
            deleted = await self.client_repository.delete(client_id)

            if not deleted:
                log.warning(
                    "Client not found for deletion",
                    extra={
                        "client_id": str(client_id),
                        "event_type": "client.delete.not_found",
                    },
                )
                raise ValueError(f"Client not found: {client_id}")

            log_business_event(
                logger=log,
                event_type="client.deleted",
                message="Client deleted successfully",
                entity_id=str(client_id),
            )

            return True

        except ValueError:
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="client.delete.unexpected_error",
                message="Unexpected error during client deletion",
                error=e,
                additional_data={"client_id": str(client_id)},
            )
            raise
