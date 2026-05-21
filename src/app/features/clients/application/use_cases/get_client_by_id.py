"""Get client by ID use case."""
from uuid import UUID

from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.application.dtos.client_dto import ClientResponse
from src.app.features.clients.application.mappers.client_mapper import to_client_response


class GetClientByIdUseCase:
    """Use case for retrieving a single client by ID."""
    
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository
    
    async def execute(self, client_id: UUID) -> ClientResponse:
        """Execute the get client by ID use case."""
        
        # Get client from repository
        client = await self.client_repository.find_by_id(client_id)
        
        if client is None:
            raise ValueError(f"Client not found: {client_id}")
        
        # Convert to response DTO using shared mapper
        return to_client_response(client)
