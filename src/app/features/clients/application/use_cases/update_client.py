"""Update client use case."""

from uuid import UUID

from src.app.features.clients.application.dtos.client_dto import ClientResponse, UpdateClientRequest
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.exceptions.client_exceptions import ClientEmailExistsError, ClientNotFoundError
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.phone_number import PhoneNumber
from src.app.shared.logging import get_logger, mask_email, set_user_id


class UpdateClientUseCase:
    """Use case for updating an existing client."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: UUID, request: UpdateClientRequest, ctx: RequestContext) -> ClientResponse:
        """Execute the update client use case."""
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        try:
            client = await self.client_repository.find_by_id(client_id, workspace_id=ctx.workspace_id.value)

            if client is None:
                log.error(
                    "Client not found for update",
                    extra={"event_type": "client.update.not_found", "entity_id": str(client_id)},
                )
                raise ClientNotFoundError(str(client_id))

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
                existing_client = await self.client_repository.find_by_email(
                    request.email, workspace_id=ctx.workspace_id.value
                )
                if existing_client:
                    log.error(
                        "Client email already exists",
                        extra={
                            "event_type": "client.update.email_exists",
                            "entity_id": str(client_id),
                            "email": mask_email(request.email),
                        },
                    )
                    raise ClientEmailExistsError(request.email)

            client.update_details(
                name=request.name,
                email=Email(request.email) if request.email else None,
                phone=PhoneNumber(request.phone) if request.phone else None,
                company=request.company,
                address=request.address,
                notes=request.notes,
            )

            updated_client = await self.client_repository.update(client)

            log.info(
                "Client updated",
                extra={
                    "event_type": "client.updated",
                    "entity_id": str(client_id),
                    "changes": changes if changes else "no_key_changes",
                },
            )

            return to_client_response(updated_client)

        except (ClientNotFoundError, ClientEmailExistsError, ValueError):
            raise
        except Exception:
            log.exception(
                "Unexpected error updating client",
                extra={"event_type": "client.update.unexpected_error", "entity_id": str(client_id)},
            )
            raise
