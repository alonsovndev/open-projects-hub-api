"""Get client by ID use case."""

from uuid import UUID

from src.app.features.clients.application.dtos.client_dto import ClientResponse
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.logging import BusinessLogger, get_logger


class GetClientByIdUseCase:
    """Use case for retrieving a single client by ID."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: UUID, user_id: str) -> ClientResponse:
        """Execute the get client by ID use case."""
        log = BusinessLogger(get_logger(__name__), user_id=user_id)

        log.info("Fetching client by ID", event_type="clients.fetch_by_id.started", client_id=str(client_id))

        client = await self.client_repository.find_by_id(client_id)

        if client is None:
            log.warning("Client not found", event_type="clients.fetch_by_id.not_found", client_id=str(client_id))
            raise ValueError(f"Client not found: {client_id}")

        log.event("clients.fetch_by_id.success", client_id=str(client_id))
        return to_client_response(client)
