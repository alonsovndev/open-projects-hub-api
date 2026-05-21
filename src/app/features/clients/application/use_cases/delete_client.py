"""Delete client use case."""
from uuid import UUID

from src.app.features.clients.domain.repositories.client_repository import ClientRepository


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
        
        # Try to delete the client
        # If client has projects, the database RESTRICT constraint will raise an error
        deleted = await self.client_repository.delete(client_id)
        
        if not deleted:
            raise ValueError(f"Client not found: {client_id}")
        
        return True
