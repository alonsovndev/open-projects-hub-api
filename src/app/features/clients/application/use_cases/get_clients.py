"""Get clients use case."""
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.application.dtos.client_dto import PaginatedClientsResponse
from src.app.features.clients.application.mappers.client_mapper import to_client_response


class GetClientsUseCase:
    """Use case for retrieving paginated clients."""
    
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository
    
    async def execute(self, offset: int = 0, limit: int = 100) -> PaginatedClientsResponse:
        """Execute the get clients use case."""
        
        clients = await self.client_repository.find_all(skip=offset, limit=limit)
        total_count = await self.client_repository.count()
        
        client_responses = [
            to_client_response(client)
            for client in clients
        ]
        
        # Calculate page number (1-indexed)
        page = (offset // limit) + 1 if limit > 0 else 1
        
        return PaginatedClientsResponse(
            items=client_responses,
            total=total_count,
            page=page,
            per_page=limit,
        )
