"""Update client use case."""

from uuid import UUID

from src.app.features.clients.application.dtos.client_dto import ClientResponse, UpdateClientRequest
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.domain.value_objects.email import Email
from src.app.features.clients.domain.value_objects.phone_number import PhoneNumber
from src.app.shared.logging import get_logger, log_business_event, log_error_event, mask_email


log = get_logger(__name__)


class UpdateClientUseCase:
    """Use case for updating an existing client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: UUID, request: UpdateClientRequest) -> ClientResponse:
        """Execute the update client use case."""
        try:
            client = await self.client_repository.find_by_id(client_id)

            if client is None:
                log.warning(
                    "Client not found for update",
                    extra={
                        "client_id": str(client_id),
                        "event_type": "client.update.not_found",
                    },
                )
                raise ValueError(f"Client not found: {client_id}")

            # Track changes for audit trail
            changes = {}
            if request.name != client.name:
                changes["name"] = {"old": client.name, "new": request.name}
            if request.email and request.email != (client.email.value if client.email else None):
                changes["email"] = {
                    "old": mask_email(client.email.value) if client.email else None,
                    "new": mask_email(request.email),
                }

            # Enforce email uniqueness when email is being changed
            if request.email and request.email != (client.email.value if client.email else None):
                existing_client = await self.client_repository.find_by_email(request.email)
                if existing_client:
                    log.warning(
                        "Client email already exists during update",
                        extra={
                            "client_id": str(client_id),
                            "email": mask_email(request.email),
                            "event_type": "client.update.email_exists",
                        },
                    )
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

            log_business_event(
                logger=log,
                event_type="client.updated",
                message="Client updated successfully",
                entity_id=str(client_id),
                additional_data={
                    "changes": changes if changes else "no_key_changes",
                },
            )

            return to_client_response(updated_client)

        except ValueError:
            raise
        except Exception as e:
            log_error_event(
                logger=log,
                error_type="client.update.unexpected_error",
                message="Unexpected error during client update",
                error=e,
                additional_data={"client_id": str(client_id)},
            )
            raise
