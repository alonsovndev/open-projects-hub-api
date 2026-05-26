"""Create client use case."""

from src.app.features.clients.application.dtos.client_dto import ClientResponse, CreateClientRequest
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.domain.repositories.client_repository import ClientRepository


class CreateClientUseCase:
    """Use case for creating a new client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, request: CreateClientRequest) -> ClientResponse:
        """Execute the create client use case."""

        # Enforce email uniqueness constraint at application layer
        if request.email:
            existing_client = await self.client_repository.find_by_email(request.email)
            if existing_client:
                raise ValueError(f"Client with email {request.email} already exists")

        client = ClientEntity.create(
            name=request.name,
            email=request.email,
            phone=request.phone,
            company=request.company,
            address=request.address,
            notes=request.notes,
        )

        saved_client = await self.client_repository.save(client)

        return to_client_response(saved_client)
