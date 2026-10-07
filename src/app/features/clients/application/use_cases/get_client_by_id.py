"""Get client by ID use case."""

from uuid import UUID

from src.app.features.clients.application.dtos.client_dto import ClientResponse
from src.app.features.clients.application.mappers.client_mapper import to_client_response
from src.app.features.clients.domain.exceptions.client_exceptions import ClientNotFoundError
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.shared.application.request_context import RequestContext
from src.app.shared.logging import get_logger, set_user_id


class GetClientByIdUseCase:
    """Use case for retrieving a single client by ID."""

    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def execute(self, client_id: UUID, ctx: RequestContext) -> ClientResponse:
        """Execute the get client by ID use case."""
        log = get_logger(__name__)
        set_user_id(str(ctx.user_id))

        try:
            log.info(
                "Fetching client by ID",
                extra={"event_type": "clients.fetch_by_id.started", "client_id": str(client_id)},
            )

            client = await self.client_repository.find_by_id(client_id, workspace_id=ctx.workspace_id.value)

            if client is None:
                log.warning(
                    "Client not found",
                    extra={"event_type": "clients.fetch_by_id.not_found", "client_id": str(client_id)},
                )
                raise ClientNotFoundError(str(client_id))

            log.info(
                "Client fetched by ID successfully",
                extra={"event_type": "clients.fetch_by_id.success", "client_id": str(client_id)},
            )
            return to_client_response(client)

        except ClientNotFoundError:
            raise
        except Exception:
            log.exception(
                "Unexpected error fetching client by ID",
                extra={"event_type": "clients.fetch_by_id.unexpected_error", "entity_id": str(client_id)},
            )
            raise
