"""Get clients use case."""

from src.app.features.clients.application.dtos.client_dto import PaginatedClientsResponse
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.logging import BusinessLogger, get_logger


class GetClientsUseCase:
    """Use case for retrieving paginated clients."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, user_id: str, offset: int = 0, limit: int = 100) -> PaginatedClientsResponse:
        """Execute the get clients use case."""
        log = BusinessLogger(get_logger(__name__), user_id=user_id)

        log.info("Listing clients", event_type="clients.list.started", offset=offset, limit=limit)

        clients = await self.client_repository.find_all(skip=offset, limit=limit)
        total_count = await self.client_repository.count()

        client_responses = [to_client_response(client) for client in clients]

        page = (offset // limit) + 1 if limit > 0 else 1

        log.event("clients.list.success", total=total_count, returned=len(client_responses))
        return PaginatedClientsResponse(
            items=client_responses,
            total=total_count,
            page=page,
            per_page=limit,
        )
