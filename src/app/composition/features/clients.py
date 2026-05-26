"""
Clients feature dependency composition.

All dependency wiring for client management use cases.

Dependencies:
- Infrastructure: Database session
- Repositories: ClientRepository (shared, also used by projects)

Use Cases:
- Create Client: Register new client organization
- List Clients: Retrieve all clients
- Get Client: Retrieve single client by ID
- Update Client: Modify client details
- Delete Client: Remove client

Cross-Feature Impact:
Projects feature depends on ClientRepository to validate client existence
when creating/updating projects. This is the only cross-feature repository
dependency in the system.

Usage:
    from src.app.composition import get_create_client_use_case

    @router.post("")
    async def create_client(
        use_case: CreateClientUseCase = Depends(get_create_client_use_case),
    ):
        return await use_case.execute(...)
"""

from fastapi import Depends

from src.app.composition.repositories import get_client_repository
from src.app.features.clients.application.use_cases.create_client import CreateClientUseCase
from src.app.features.clients.application.use_cases.delete_client import DeleteClientUseCase
from src.app.features.clients.application.use_cases.get_client_by_id import GetClientByIdUseCase
from src.app.features.clients.application.use_cases.get_clients import GetClientsUseCase
from src.app.features.clients.application.use_cases.update_client import UpdateClientUseCase
from src.app.features.clients.domain.repositories.client_repository import ClientRepository


# Use case factories
async def get_create_client_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> CreateClientUseCase:
    """CreateClientUseCase factory."""
    return CreateClientUseCase(repository)


async def get_get_clients_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> GetClientsUseCase:
    """GetClientsUseCase factory."""
    return GetClientsUseCase(repository)


async def get_get_client_by_id_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> GetClientByIdUseCase:
    """GetClientByIdUseCase factory."""
    return GetClientByIdUseCase(repository)


async def get_update_client_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> UpdateClientUseCase:
    """UpdateClientUseCase factory."""
    return UpdateClientUseCase(repository)


async def get_delete_client_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> DeleteClientUseCase:
    """DeleteClientUseCase factory."""
    return DeleteClientUseCase(repository)
