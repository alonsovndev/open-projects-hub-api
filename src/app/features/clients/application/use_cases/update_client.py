"""Update client use case."""
from uuid import UUID

from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.domain.value_objects.email import Email
from src.app.features.clients.domain.value_objects.phone_number import PhoneNumber
from src.app.features.clients.application.dtos.client_dto import UpdateClientRequest, ClientResponse
from src.app.features.clients.application.mappers.client_mapper import to_client_response


class UpdateClientUseCase:
    """Use case for updating an existing client."""
    
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository
    
    async def execute(self, client_id: UUID, request: UpdateClientRequest) -> ClientResponse:
        """Execute the update client use case."""
        
        client = await self.client_repository.find_by_id(client_id)
        
        if client is None:
            raise ValueError(f"Client not found: {client_id}")
        
        # Enforce email uniqueness when email is being changed
        if request.email and request.email != (client.email.value if client.email else None):
            existing_client = await self.client_repository.find_by_email(request.email)
            if existing_client:
                raise ValueError(f"Client with email {request.email} already exists")
        
        client.update_details(
            name=request.name,
            email=Email(request.email) if request.email else None,
            phone=PhoneNumber(request.phone) if request.phone else None,
            company=request.company,
            address=request.address,
            notes=request.notes,
        )
        
        updated_client = await self.client_repository.update(client)
        
        return to_client_response(updated_client)
