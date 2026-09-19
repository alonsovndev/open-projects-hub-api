"""Delete client use case."""

from uuid import UUID

from src.app.features.clients.domain.exceptions.client_exceptions import (
    ClientHasActiveProjectsError,
    ClientNotFoundError,
)
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.logging import get_logger, set_user_id


class DeleteClientUseCase:
    """Use case for deleting a client."""

    def __init__(self, client_repository: ClientRepository, project_repository: ProjectRepository):
        self.client_repository = client_repository
        self.project_repository = project_repository

    async def execute(self, client_id: UUID, created_by: str) -> bool:
        """Execute the delete client use case.

        Clients with active projects cannot be deleted. Archived projects
        belonging to the client are deleted first, then the client itself.

        Args:
            client_id: UUID of the client to delete.
            created_by: User ID performing the deletion.

        Returns:
            bool: True if client was deleted.

        Raises:
            ClientHasActiveProjectsError: If the client still has active projects.
            ClientNotFoundError: If the client does not exist.
        """
        log = get_logger(__name__)
        set_user_id(created_by)

        try:
            if await self.project_repository.has_active_projects_for_client(client_id):
                log.warning(
                    "Client deletion blocked: active projects exist",
                    extra={
                        "event_type": "client.delete.blocked_active_projects",
                        "entity_id": str(client_id),
                    },
                )
                raise ClientHasActiveProjectsError(str(client_id))

            deleted_archived = await self.project_repository.delete_archived_by_client(client_id)
            if deleted_archived:
                log.info(
                    "Deleted archived projects before client deletion",
                    extra={
                        "event_type": "client.delete.archived_projects_removed",
                        "entity_id": str(client_id),
                        "projects_deleted": deleted_archived,
                    },
                )

            deleted = await self.client_repository.delete(client_id)

            if not deleted:
                log.error(
                    "Client not found for deletion",
                    extra={"event_type": "client.delete.not_found", "entity_id": str(client_id)},
                )
                raise ClientNotFoundError(str(client_id))

            log.info("Client deleted", extra={"event_type": "client.deleted", "entity_id": str(client_id)})

            return True

        except (ClientNotFoundError, ClientHasActiveProjectsError):
            raise
        except Exception:
            log.exception(
                "Unexpected error deleting client",
                extra={"event_type": "client.delete.unexpected_error", "entity_id": str(client_id)},
            )
            raise
