"""Create client use case."""

from src.app.features.clients.application.dtos.client_dto import ClientResponse, CreateClientRequest
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.domain.exceptions.client_exceptions import ClientEmailExistsError
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.logging import get_logger, mask_email, set_user_id


class CreateClientUseCase:
    """Use case for creating a new client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, request: CreateClientRequest, created_by: str) -> ClientResponse:
        """Execute the create client use case."""
        log = get_logger(__name__)
        set_user_id(created_by)

        try:
            # Enforce email uniqueness constraint at application layer
            if request.email:
                existing_client = await self.client_repository.find_by_email(request.email)
                if existing_client:
                    log.error(
                        "Client email already exists",
                        extra={
                            "event_type": "client.create.email_exists",
                            "entity_id": str(existing_client.id),
                            "email": mask_email(request.email),
                        },
                    )
                    raise ClientEmailExistsError(request.email)

            client = ClientEntity.create(
                name=request.name,
                email=request.email,
                phone=request.phone,
                company=request.company,
                address=request.address,
                notes=request.notes,
            )

            saved_client = await self.client_repository.save(client)

            log.info(
                "Client created",
                extra={
                    "event_type": "client.created",
                    "entity_id": str(saved_client.id.value),
                    "client_name": saved_client.name,
                    "email": mask_email(saved_client.email.value) if saved_client.email else None,
                    "company": saved_client.company,
                },
            )

            return to_client_response(saved_client)

        except (ValueError, ClientEmailExistsError):
            raise
        except Exception:
            log.exception(
                "Unexpected error creating client",
                extra={
                    "event_type": "client.create.unexpected_error",
                    "entity_id": str(saved_client.id) if saved_client else None,
                },
            )
            raise
