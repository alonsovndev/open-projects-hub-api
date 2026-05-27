"""Create client use case."""

from src.app.features.clients.application.dtos.client_dto import ClientResponse, CreateClientRequest
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.logging import get_logger, log_business_event, log_error_event, mask_email


log = get_logger(__name__)


class CreateClientUseCase:
    """Use case for creating a new client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, request: CreateClientRequest) -> ClientResponse:
        """Execute the create client use case."""
        try:
            # Enforce email uniqueness constraint at application layer
            if request.email:
                existing_client = await self.client_repository.find_by_email(request.email)
                if existing_client:
                    log.warning(
                        "Client email already exists",
                        extra={
                            "email": mask_email(request.email),
                            "event_type": "client.create.email_exists",
                        },
                    )
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

            log_business_event(
                logger=log,
                event_type="client.created",
                message="Client created successfully",
                entity_id=str(saved_client.id.value),
                additional_data={
                    "name": saved_client.name,
                    "email": mask_email(saved_client.email.value) if saved_client.email else None,
                    "company": saved_client.company,
                },
            )

            return to_client_response(saved_client)

        except ValueError:
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="client.create.unexpected_error",
                message="Unexpected error during client creation",
                error=e,
            )
            raise
